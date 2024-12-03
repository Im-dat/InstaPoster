# pyright: reportMissingImports=false
from instagrapi import Client  # Cliente principal para API do Instagram
import os  # Operações do sistema operacional
import time  # Para delays entre operações
from PIL import Image # type: ignore  # Manipulação de imagens
import sys  # Funcionalidades do sistema
import logging  # Sistema de logs
import requests  # Requisições HTTP
from dotenv import load_dotenv  # Carregamento de variáveis de ambiente
import subprocess  # Execução de processos
import argparse  # Parse de argumentos da linha de comando
from colorama import init, Fore  # Cores no terminal
import locale  # Configurações regionais
import json  # Manipulação de JSON
from datetime import datetime  # Manipulação de datas
from cryptography.fernet import Fernet  # Criptografia
import base64  # Codificação base64
from moviepy.editor import VideoFileClip

# Após os imports, antes de iniciar o processamento
try:
    import moviepy.editor
    moviepy_installed = True
except ImportError:
    moviepy_installed = False

# Configura encoding para UTF-8
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

# Inicializa colorama para cores no Windows
init()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('instagram_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

def get_system_language():
    try:
        locale.setlocale(locale.LC_ALL, '')
        lang = locale.getlocale()[0]
        return lang if lang else 'en_US'
    except:
        return 'en_US'

# Mensagens em diferentes idiomas
MESSAGES = {
    'pt_BR': {
        'login_success': '[OK] Login realizado com sucesso!',
        'login_error': 'Erro ao fazer login: {}',
        'missing_env': 'Erro: Arquivo .env não encontrado ou variáveis de ambiente não configuradas!',
        'connection_error': 'Erro: Não foi possível conectar ao Instagram. Verifique sua conexão.',
        'dep_check': 'Verificando dependências...',
        'dep_missing': 'Dependência {} não encontrada. Instalando...',
        'dep_installed': '[OK] Todas as dependências estão instaladas.',
        'video_too_long': 'Vídeo muito longo ({}s). O Instagram aceita apenas vídeos de até 60 segundos.',
        'video_too_large': 'Vídeo muito grande ({}MB). O Instagram tem um limite de 100MB.',
        'processing_media': 'Processando mídia: {}',
        'upload_success': '[OK] Mídia postada com sucesso: {}',
        'waiting': 'Aguardando {} segundos antes do próximo post...',
        'video_processing': 'Preparando vídeo para upload...',
        'video_skipped': 'Vídeo ignorado: MoviePy não está instalado',
    },
    'en_US': {
        'login_success': '[OK] Login successful!',
        'login_error': 'Login error: {}',
        'missing_env': 'Error: .env file not found or environment variables not set!',
        'connection_error': 'Error: Could not connect to Instagram. Check your connection.',
        'dep_check': 'Checking dependencies...',
        'dep_missing': 'Dependency {} not found. Installing...',
        'dep_installed': '[OK] All dependencies are installed.',
        'video_too_long': 'Video too long ({}s). Instagram only accepts videos up to 60 seconds.',
        'video_too_large': 'Video too large ({}MB). Instagram has a 100MB limit.',
        'processing_media': 'Processing media: {}',
        'upload_success': '[OK] Media posted successfully: {}',
        'waiting': 'Waiting {} seconds before next post...',
        'video_processing': 'Preparing video for upload...',
        'video_skipped': 'Video skipped: MoviePy not installed',
    }
}

# Detecta idioma do sistema
SYSTEM_LANG = get_system_language()

def get_message(key):
    """Retorna mensagem no idioma do sistema ou em inglês como fallback"""
    messages = MESSAGES.get(SYSTEM_LANG, MESSAGES['en_US'])
    return messages.get(key, MESSAGES['en_US'][key])

def check_dependencies():
    """Verifica e instala dependências necessárias"""
    logger.info(get_message('dep_check'))
    required_packages = {
        'instagrapi': 'instagrapi',
        'PIL': 'Pillow',
        'moviepy': 'moviepy',
        'dotenv': 'python-dotenv',
        'requests': 'requests'
    }
    
    for module, package in required_packages.items():
        try:
            __import__(module)
        except ImportError:
            logger.warning(get_message('dep_missing').format(package))
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    logger.info(get_message('dep_installed'))

def check_instagram_connection():
    """Verifica a conexão com o Instagram"""
    try:
        response = requests.get('https://www.instagram.com', timeout=5)
        return response.status_code == 200
    except:
        return False

def resize_image(image_path):
    """Redimensiona a imagem para as dimensões aceitas pelo Instagram"""
    try:
        with Image.open(image_path) as img:
            max_size = (1080, 1080)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            output_path = f"{image_path}_resized.jpg"
            img.save(output_path, "JPEG", quality=95)
            return output_path
    except Exception as e:
        print(f"Erro ao redimensionar imagem: {e}")
        return image_path

def is_valid_image(filepath):
    try:
        with Image.open(filepath) as img:
            return img.format in ['JPEG', 'PNG']
    except:
        return False

def is_valid_video(filepath):
    """Verifica se o arquivo é um vídeo válido"""
    video_extensions = ['.mp4', '.mov', '.avi']
    return os.path.splitext(filepath)[1].lower() in video_extensions

def get_or_create_key():
    """Obtém ou cria uma chave de criptografia"""
    key_file = '.secret.key'
    if os.path.exists(key_file):
        with open(key_file, 'rb') as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(key_file, 'wb') as f:
            f.write(key)
        return key

def encrypt_credentials(username, password):
    """Criptografa as credenciais"""
    key = get_or_create_key()
    f = Fernet(key)
    credentials = f"{username}:{password}".encode()
    return f.encrypt(credentials)

def decrypt_credentials():
    """Descriptografa as credenciais"""
    try:
        key = get_or_create_key()
        f = Fernet(key)
        with open('.credentials.enc', 'rb') as file:
            encrypted_data = file.read()
        decrypted_data = f.decrypt(encrypted_data).decode()
        username, password = decrypted_data.split(':')
        return username, password
    except FileNotFoundError:
        return None, None

def login(cl):
    """Realiza login no Instagram usando credenciais criptografadas"""
    usuario = os.getenv('INSTAGRAM_USER')
    senha = os.getenv('INSTAGRAM_PASSWORD')
    
    if not usuario or not senha:
        usuario, senha = decrypt_credentials()
    if not usuario or not senha:
        logger.error(get_message('missing_env'))
        return False
        
    if not check_instagram_connection():
        logger.error(get_message('connection_error'))
        return False
    
    try:
        logger.info(f"Tentando fazer login como {usuario}...")
        cl.login(usuario, senha)
        logger.info(get_message('login_success'))
        return True
    except Exception as e:
        logger.error(get_message('login_error').format(str(e)))
        return False

def load_posted_media():
    """Carrega o registro de mídias já postadas"""
    try:
        with open('posted_media.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_posted_media(media_path):
    """Salva registro de mídia postada"""
    posted = load_posted_media()
    posted[os.path.basename(media_path)] = {
        'timestamp': datetime.now().isoformat(),
        'path': media_path
    }
    with open('posted_media.json', 'w') as f:
        json.dump(posted, f, indent=2)

def postar_midia(cl):
    try:
        arquivos = os.listdir(CAMINHO_ARQUIVOS)
        posted_media = load_posted_media()
        
        # Filtra arquivos já postados
        arquivos = [f for f in arquivos if f not in posted_media]
        
        logger.info(f"Encontrados {len(arquivos)} arquivos não postados no diretório")
        
        if not arquivos:
            logger.info("Nenhum arquivo novo para postar. Encerrando...")
            return
        
        posts_realizados = 0
        for arquivo in arquivos:
            caminho_arquivo = os.path.join(CAMINHO_ARQUIVOS, arquivo)
            print(f"\nProcessando arquivo: {arquivo}")
            
            if is_valid_image(caminho_arquivo):
                print("Arquivo é uma imagem válida")
                try:
                    print("Redimensionando imagem...")
                    resized_image = resize_image(caminho_arquivo)
                    
                    print(f"Tentando fazer upload da foto: {resized_image}")
                    print(f"Tamanho do arquivo: {os.path.getsize(resized_image) / (1024 * 1024):.2f} MB")
                    
                    try:
                        media = cl.photo_upload(
                            resized_image,
                            caption=CAPTION_PADRAO
                        )
                        print(f"✓ Foto postada com sucesso: {arquivo}")
                        posts_realizados += 1
                    except Exception as upload_error:
                        print(f"Erro específico durante upload: {str(upload_error)}")
                        print(f"Tipo do erro: {type(upload_error)}")
                        print(f"Detalhes completos: {repr(upload_error)}")
                    
                    if resized_image != caminho_arquivo:
                        print("Removendo arquivo temporário...")
                        os.remove(resized_image)
                    
                except Exception as e:
                    print(f"Erro ao processar foto {arquivo}: {str(e)}")
                    print(f"Detalhes completos: {repr(e)}")
                    
            elif is_valid_video(caminho_arquivo):
                if not moviepy_installed: # type: ignore
                    print("Pulando vídeo pois moviepy não está instalado")
                    continue
                    
                print("Arquivo é um vídeo válido")
                try:
                    print("Iniciando upload do vídeo...")
                    try:
                        # Verify video can be loaded with moviepy
                        print(f"Verificando vídeo: {caminho_arquivo}")
                        video = VideoFileClip(caminho_arquivo)
                        duration = video.duration
                        size_mb = os.path.getsize(caminho_arquivo) / (1024 * 1024)  # Tamanho em MB
                        print(f"Duração do vídeo: {duration:.1f} segundos")
                        print(f"Tamanho do arquivo: {size_mb:.1f} MB")
                        video.close()
                        
                        if duration > 60:
                            print(f"Vídeo muito longo ({duration:.1f}s). Pulando...")
                            continue
                            
                        if size_mb > 100:  # Instagram geralmente tem limite de ~100MB
                            print(f"Vídeo muito grande ({size_mb:.1f}MB). Pulando...")
                            continue
                            
                    except Exception as e:
                        print(f"Erro ao processar vídeo: {str(e)}")
                        print("Verifique se o vídeo está corrompido ou em formato incompatível")
                        continue

                    print("Tentando upload para o Instagram...")
                    try:
                        print("Convertendo vídeo para formato compatível...")
                        video_path = convert_video(caminho_arquivo)
                        
                        print("Tentando upload para o Instagram...")
                        media = cl.video_upload(
                            video_path,
                            caption=CAPTION_PADRAO
                        )
                        
                        # Limpa o arquivo convertido se foi criado
                        if video_path != caminho_arquivo:
                            os.remove(video_path)
                            
                        print(f"✓ Vídeo postado com sucesso: {arquivo}")
                        posts_realizados += 1
                    except Exception as e:
                        print(f"Erro durante upload do vídeo: {str(e)}")
                        print("Detalhes do erro:", repr(e))
                        
                except Exception as e:
                    print(f"Erro ao postar vídeo {arquivo}: {str(e)}")
                    print("Erro completo:", repr(e))
            else:
                print(f"Arquivo ignorado (não é uma mídia válida): {arquivo}")
            
            if posts_realizados < len(arquivos):
                tempo_espera = 30 if is_valid_video(caminho_arquivo) else 10
                print(f"Aguardando {tempo_espera} segundos antes do próximo post...")
                time.sleep(tempo_espera)
                
        print("\nProcessamento concluído!")
        print(f"Total de posts realizados: {posts_realizados}")
        
    except KeyboardInterrupt:
        print("\nOperação interrompida pelo usuário")
        print(f"Total de posts realizados antes da interrupção: {posts_realizados}")
    except Exception as e:
        print(f"Erro geral: {str(e)}")

def convert_video(input_path):
    """Converte o vídeo para um formato compatível com o Instagram"""
    try:
        output_path = input_path + "_converted.mp4"
        print("Convertendo vídeo para formato compatível...")
        
        video = VideoFileClip(input_path)
        video.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True
        )
        video.close()
        
        return output_path
    except Exception as e:
        print(f"Erro ao converter vídeo: {str(e)}")
        return input_path

def parse_arguments():
    """Parse argumentos da linha de comando"""
    parser = argparse.ArgumentParser(description='Instagram Auto Poster')
    parser.add_argument('--caption', type=str, help='Caption personalizada para os posts')
    parser.add_argument('--path', type=str, help='Caminho para a pasta com as mídias')
    return parser.parse_args()

if __name__ == "__main__":
    try:
        # Verifica dependências
        check_dependencies()
        
        # Parse argumentos
        args = parse_arguments()
        
        # Configura caminho e caption
        CAMINHO_ARQUIVOS = args.path or os.getenv('MEDIA_PATH', r"LOCAL DA PASTA AQUI")
        CAPTION_PADRAO = args.caption or os.getenv('DEFAULT_CAPTION', "Postado automaticamente. #automacao")
        
        if not os.path.exists(CAMINHO_ARQUIVOS):
            logger.error(f"Erro: O diretório {CAMINHO_ARQUIVOS} não existe!")
            sys.exit(1)
            
        logger.info(f"Usando diretório de mídia: {CAMINHO_ARQUIVOS}")
        
        cl = Client()
        
        if login(cl):
            postar_midia(cl)
        else:
            logger.error("Não foi possível fazer login. Encerrando programa.")
    except KeyboardInterrupt:
        logger.info("\nPrograma encerrado pelo usuário")
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
