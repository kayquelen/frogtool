from commenter import CommentBot
import logging
import json
import time
import random
from concurrent.futures import ThreadPoolExecutor
from typing import List
import queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MassCommenter:
    def __init__(self, config_file: str, max_threads: int = 10):
        self.config_file = config_file
        self.max_threads = max_threads
        self.jwt_tokens = []
        self.comments = []
        self.mint_ids = []
        self.token_queue = queue.Queue()
        self.load_config()
        
    def load_config(self):
        """Carrega configuração do arquivo JSON"""
        logger.info(f"Carregando configuração de {self.config_file}")
        with open(self.config_file, "r") as f:
            config = json.load(f)
            self.jwt_tokens = config['jwt_tokens']
            self.comments = config.get('comments', ["Awesome project! 🚀"])
            self.mint_ids = config.get('mint_ids', [])
            self.proxy = config.get('proxy', {
                'host': 'rotating-proxy.example.com',
                'port': 8080,
                'username': 'user',
                'password': 'pass',
                'protocol': 'http'
            })
            
        # Coloca todos os tokens na fila
        for token in self.jwt_tokens:
            self.token_queue.put(token)
            
        logger.info(f"Configuração carregada: {len(self.jwt_tokens)} tokens, {len(self.comments)} comentários, {len(self.mint_ids)} mints")

    def get_next_token(self) -> str:
        """Pega próximo token da fila e o coloca no final"""
        token = self.token_queue.get()
        self.token_queue.put(token)  # Coloca de volta no final da fila
        return token

    def comment_worker(self, mint_id: str):
        """Worker function para cada thread"""
        try:
            # Pega um token da fila
            jwt_token = self.get_next_token()
            
            # Escolhe um comentário aleatório
            comment = random.choice(self.comments)
            
            # Cria uma instância do bot sem passar JWT token diretamente
            bot = CommentBot(
                jwt_token=jwt_token,
                delay_range=(1, 2),  # Delay menor para mais velocidade
                proxies=[self.proxy]  # Usa o proxy rotativo
            )
            
            try:
                logger.info(f"Comentando no mint {mint_id}")
                success = bot.post_comment(mint_id, comment)
                
                if success:
                    logger.info(f"✅ Sucesso no mint {mint_id}")
                else:
                    logger.error(f"❌ Falha no mint {mint_id}")
                    
            finally:
                bot.close()
                
        except Exception as e:
            logger.error(f"Erro no worker: {str(e)}")

    def start_commenting(self):
        """Inicia o processo de comentários em massa"""
        logger.info("Iniciando comentários em massa...")
        
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            # Submete todos os mints para processamento
            futures = [executor.submit(self.comment_worker, mint_id) 
                      for mint_id in self.mint_ids]
            
            # Aguarda todos terminarem
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Erro em uma thread: {str(e)}")

if __name__ == "__main__":
    # Exemplo de uso
    mass_commenter = MassCommenter(
        config_file="config.json",
        max_threads=10  # Ajuste conforme necessário
    )
    mass_commenter.start_commenting()
