# pyright: reportMissingImports=false
from instagrapi import Client
import os
import time
from PIL import Image
import sys

# Tentativa alternativa de importar moviepy
try:
    import moviepy
    from moviepy.editor import VideoFileClip
    moviepy_installed = True
    print(f"✓ moviepy {moviepy.__version__} importado com sucesso")
except ImportError as e:
    print(f"Erro ao importar moviepy. Instale usando as instruções em redmi.txt")
    print(f"Erro detalhado: {e}")
    moviepy_installed = False
    VideoFileClip = None

# Configurações
USUARIO = "tambosi@protonmail.ch"
SENHA = "OriDDovIWzC3RY"
CAMINHO_ARQUIVOS = r"C:\Users\Anderson Tambosi\Desktop\gg"
CAPTION_PADRAO = "Postado automaticamente. #automacao"

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

def login(cl):
    try:
        print(f"Tentando fazer login como {USUARIO}...")
        cl.login(USUARIO, SENHA)
        print("✓ Login realizado com sucesso!")
        return True
    except Exception as e:
        print(f"Erro ao fazer login: {str(e)}")
        print("Dicas de solução:")
        print("1. Verifique se as credenciais estão corretas")
        print("2. Tente fazer login manual no Instagram web primeiro")
        print("3. Aguarde alguns minutos e tente novamente")
        print("4. Verifique se não há captcha ou verificação de 2 fatores pendente")
        return False

def postar_midia(cl):
    try:
        arquivos = os.listdir(CAMINHO_ARQUIVOS)
        print(f"Encontrados {len(arquivos)} arquivos no diretório")
        
        if not arquivos:
            print("Nenhum arquivo encontrado no diretório. Encerrando...")
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
                if not moviepy_installed:
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

if __name__ == "__main__":
    try:
        if not os.path.exists(CAMINHO_ARQUIVOS):
            print(f"Erro: O diretório {CAMINHO_ARQUIVOS} não existe!")
            sys.exit(1)
            
        print(f"Usando diretório de mídia: {CAMINHO_ARQUIVOS}")
        
        cl = Client()
        
        if login(cl):
            postar_midia(cl)
        else:
            print("Não foi possível fazer login. Encerrando programa.")
    except KeyboardInterrupt:
        print("\nPrograma encerrado pelo usuário")
    except Exception as e:
        print(f"Erro inesperado: {e}")
