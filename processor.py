import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List
from exceptions import MediaProcessingException

logger = logging.getLogger(__name__)

class MediaProcessor:
    def __init__(self, config):
        self.config = config
        self.executor = ThreadPoolExecutor(max_workers=config.max_workers)
        self.logger = logging.getLogger(__name__)
    
    def _validate_file(self, file: Path) -> bool:
        """Valida se o arquivo é uma mídia permitida"""
        if not file.exists():
            return False
        
        suffix = file.suffix.lower()
        if suffix in self.config.allowed_image_formats:
            return True
        if suffix in self.config.allowed_video_formats:
            size = file.stat().st_size
            if size > self.config.max_video_size:
                self.logger.warning(f"Vídeo muito grande: {file}")
                return False
            return True
        return False
    
    async def process_directory(self, directory: Path) -> List[Path]:
        """Processa arquivos de mídia em paralelo"""
        self.logger.info(f"Processando diretório: {directory}")
        files = [f for f in directory.glob("**/*.*") if self._validate_file(f)]
        
        if not files:
            self.logger.warning("Nenhum arquivo válido encontrado")
            return []
        
        tasks = [asyncio.create_task(self.process_file(f)) for f in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        errors = [r for r in results if isinstance(r, Exception)]
        if errors:
            self.logger.error(f"Erros no processamento: {errors}")
            raise MediaProcessingException(f"Erros no processamento", str(directory), {"errors": errors})
        
        return [r for r in results if isinstance(r, Path)]
    
    async def process_file(self, file: Path) -> Path:
        """Processa um arquivo individual"""
        try:
            # Executa o processamento pesado em uma thread separada
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._process_file_sync,
                file
            )
            return result
        except Exception as e:
            raise MediaProcessingException(f"Erro ao processar {file}: {e}")
    
    def _process_file_sync(self, file: Path) -> Path:
        # Implementar lógica de processamento específica aqui
        return file 