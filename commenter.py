import logging
import random
import time
from threading import Thread
from typing import List, Optional, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import json
import zipfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CommentBot:
    def __init__(
        self,
        config_path: str = 'config.json',
        delay_range: tuple = (1, 3),
        proxies: List[Dict] = None
    ):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        self.jwt_tokens = self.config['jwt_tokens']
        self.delay_range = delay_range
        self.proxies = proxies
        self.base_url = "https://pump.fun"
        self.driver = None
        self.short_wait = None
        self.long_wait = None
        
        # Inicializa o driver
        self.setup_driver()
        
        # Fazer login via cookie JWT
        self.setup_authentication()
        
    def get_random_jwt(self):
        """Retorna um token JWT aleatório da lista de tokens"""
        return random.choice(self.jwt_tokens)
        
    def setup_authentication(self):
        """Configura a autenticação via cookie JWT"""
        logger.info("Configurando autenticação...")
        
        jwt_token = self.get_random_jwt()
        
        # Primeiro acessa a página e clica no I'm ready
        self.driver.get("https://pump.fun")
        time.sleep(0.5)  # Reduzir espera inicial
        
        try:
            # Clicar no "I'm ready to pump" antes de autenticar
            logger.info("Procurando botão 'I'm ready to pump'...")
            ready_button = self.short_wait.until(
                EC.element_to_be_clickable((
                    By.CSS_SELECTOR, 
                    "button[data-sentry-element='Button'][data-sentry-source-file='HowItWorks.tsx']"
                ))
            )
            ready_button.click()
            logger.info("Botão 'I'm ready to pump' clicado")
        except Exception as e:
            logger.warning(f"Botão 'I'm ready' não encontrado, continuando mesmo assim: {e}")
            
        # Agora adiciona o cookie JWT
        try:
            logger.info("Adicionando cookie JWT...")
            self.driver.delete_all_cookies()
            self.driver.add_cookie({
                'name': 'auth_token',
                'value': jwt_token,
                'domain': 'pump.fun',
                'path': '/'
            })
            logger.info("Cookie JWT adicionado")
            
            # Recarregar página para aplicar o cookie
            self.driver.refresh()
            logger.info("Página recarregada com autenticação")
            
        except Exception as e:
            logger.error(f"Erro ao adicionar cookie: {str(e)}")
            raise
            
    def setup_driver(self):
        # Configurar o Chrome
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Configurações experimentais
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Disable Google services and optimization
        chrome_options.add_argument('--disable-features=OptimizationHints')
        chrome_options.add_argument('--disable-features=OptimizationGuideModelDownloading')
        chrome_options.add_argument('--disable-features=OptimizationHintsFetching')
        chrome_options.add_argument('--disable-features=OptimizationTargetPrediction')
        chrome_options.add_argument('--disable-domain-reliability')
        chrome_options.add_argument('--disable-breakpad')
        chrome_options.add_argument('--disable-component-update')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--disable-sync')
        chrome_options.add_argument('--disable-background-networking')
        chrome_options.add_argument('--disable-features=OptimizationGuideModelDownloading,OptimizationHintsFetching,OptimizationTargetPrediction')

        # Block specific domains
        prefs = {
            'profile.managed_default_content_settings.images': 2,  # Disable images
            'profile.default_content_setting_values': {
                'images': 2,
                'plugins': 2,
                'popups': 2,
                'geolocation': 2,
                'notifications': 2,
                'auto_select_certificate': 2,
                'fullscreen': 2,
                'mouselock': 2,
                'mixed_script': 2,
                'media_stream': 2,
                'media_stream_mic': 2,
                'media_stream_camera': 2,
                'protocol_handlers': 2,
                'ppapi_broker': 2,
                'automatic_downloads': 2,
                'midi_sysex': 2,
                'push_messaging': 2,
                'ssl_cert_decisions': 2,
                'metro_switch_to_desktop': 2,
                'protected_media_identifier': 2,
                'app_banner': 2,
                'site_engagement': 2,
                'durable_storage': 2
            },
            # Block Google optimization domains
            'profile.block_third_party_cookies': True,
            'profile.default_content_settings.cookies': 2,
            'profile.cookie_controls_mode': 2,
            'profile.block_third_party_urls': [
                "optimizationguide-pa.googleapis.com",
                "*.googleapis.com",
                "*.google.com",
                "*.gstatic.com",
                "*.googleusercontent.com"
            ]
        }
        chrome_options.add_experimental_option('prefs', prefs)
        
        # Additional performance settings
        chrome_options.add_argument('--disable-features=site-per-process')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        chrome_options.add_argument('--disable-site-isolation-trials')
        chrome_options.add_argument('--disable-features=TranslateUI')
        chrome_options.add_argument('--disable-translate')
        chrome_options.add_argument('--disable-features=Translate')
        
        # Configurar proxy se disponível
        if self.proxies:
            proxy = self.get_random_proxy()
            if proxy:
                # Configurar proxy com autenticação
                manifest_json = """
                {
                    "version": "1.0.0",
                    "manifest_version": 2,
                    "name": "Chrome Proxy",
                    "permissions": [
                        "proxy",
                        "tabs",
                        "unlimitedStorage",
                        "storage",
                        "<all_urls>",
                        "webRequest",
                        "webRequestBlocking"
                    ],
                    "background": {
                        "scripts": ["background.js"]
                    },
                    "minimum_chrome_version":"22.0.0"
                }
                """

                background_js = """
                var config = {
                        mode: "fixed_servers",
                        rules: {
                        singleProxy: {
                            scheme: "http",
                            host: "%s",
                            port: parseInt(%s)
                        },
                        bypassList: ["localhost"]
                        }
                    };

                chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

                function callbackFn(details) {
                    return {
                        authCredentials: {
                            username: "%s",
                            password: "%s"
                        }
                    };
                }

                chrome.webRequest.onAuthRequired.addListener(
                            callbackFn,
                            {urls: ["<all_urls>"]},
                            ['blocking']
                );
                """ % (proxy['host'], proxy['port'], proxy['username'], proxy['password'])

                pluginfile = 'proxy_auth_plugin.zip'
                with zipfile.ZipFile(pluginfile, 'w') as zp:
                    zp.writestr("manifest.json", manifest_json)
                    zp.writestr("background.js", background_js)
                
                chrome_options.add_extension(pluginfile)
                logger.info(f"Proxy configurado: {proxy['host']}:{proxy['port']}")
        
        # Inicializar o driver com retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                self.driver.set_page_load_timeout(30)
                self.driver.implicitly_wait(10)
                logger.info("Chrome iniciado com sucesso")
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Falha ao iniciar Chrome após {max_retries} tentativas: {str(e)}")
                    raise
                logger.warning(f"Tentativa {attempt + 1} falhou, tentando novamente...")
                time.sleep(2)
        
        self.short_wait = WebDriverWait(self.driver, 1)  # Espera curta de 1 segundo
        self.long_wait = WebDriverWait(self.driver, 2)  # Máximo 2 segundos de espera
        
    def random_delay(self):
        """Adiciona um delay aleatório para simular comportamento humano"""
        time.sleep(random.uniform(*self.delay_range))
    
    def load_tokens(self, tokens_file: str) -> List[str]:
        """Load JWT tokens from a file."""
        try:
            with open(tokens_file, 'r') as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            logger.error(f"Error loading tokens: {e}")
            return []

    def get_random_proxy(self) -> Optional[Dict[str, str]]:
        """Get a random proxy from the proxy list."""
        return random.choice(self.proxies) if self.proxies else None

    def clean_mint_id(self, mint_id):
        """Limpa o mint ID removendo URLs duplicadas e extraindo apenas o ID"""
        import re
        
        # Primeiro tenta encontrar o mint ID no formato padrão
        match = re.search(r'[A-Za-z0-9]{44}pump', mint_id)
        if match:
            clean_id = match.group(0)
            logger.info(f"URL original: {mint_id}")
            logger.info(f"Mint ID limpo: {clean_id}")
            return clean_id
            
        # Se não encontrou, tenta limpar URLs duplicadas
        if "pump.fun/coin/" in mint_id:
            parts = mint_id.split("pump.fun/coin/")
            # Pega a última parte após pump.fun/coin/
            last_part = parts[-1]
            # Procura o mint ID nesta última parte
            match = re.search(r'[A-Za-z0-9]{44}pump', last_part)
            if match:
                clean_id = match.group(0)
                logger.info(f"URL original: {mint_id}")
                logger.info(f"Mint ID limpo: {clean_id}")
                return clean_id
                
        logger.error(f"Não foi possível extrair um mint ID válido de: {mint_id}")
        return mint_id

    def post_comment(self, mint_id, comment_text):
        """Posta um comentário em um mint específico."""
        try:
            # Limpa o mint ID primeiro
            mint_id = self.clean_mint_id(mint_id)
            logger.info(f"Mint ID limpo: {mint_id}")
            
            # Constrói a URL correta
            url = f"https://pump.fun/coin/{mint_id}"
            logger.info(f"Acessando URL: {url}")
            
            max_retries = 2  # Reduzir número de tentativas
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    # Navegar direto para a página do mint
                    self.driver.get(url)
                    time.sleep(0.5)  # Reduzir espera para meio segundo
                    
                    # Remover elemento fixo que está bloqueando
                    self.driver.execute_script("""
                        var element = document.querySelector('.fixed.bottom-0');
                        if(element) element.remove();
                    """)
                    
                    # Tentar diferentes seletores para o botão de comentário
                    logger.info("Procurando botão de comentário...")
                    selectors = [
                        "div.flex.items-center.gap-1.ml-2.px-2.cursor-pointer.bg-green-300.text-black.rounded-md.py-1",
                        "[data-sentry-element='CommentButton']",
                        "div[role='button']",
                        "div.cursor-pointer:has(svg)"
                    ]
                    
                    comment_button = None
                    for selector in selectors:
                        try:
                            comment_button = self.short_wait.until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                            if comment_button:
                                break
                        except:
                            continue
                    
                    if not comment_button:
                        retry_count += 1
                        logger.warning(f"Botão não encontrado, tentativa {retry_count} de {max_retries}")
                        time.sleep(0.2)
                        continue
                    
                    # Tentar clicar no botão imediatamente com JavaScript
                    try:
                        logger.info("Tentando clicar com JavaScript...")
                        self.driver.execute_script("arguments[0].click();", comment_button)
                    except Exception as e:
                        logger.error(f"Erro ao clicar no botão: {str(e)}")
                        retry_count += 1
                        continue
                        
                    logger.info("Botão de comentário clicado")
                    time.sleep(0.2)
                    
                    # Esperar a textarea aparecer e tentar clicar imediatamente
                    logger.info("Procurando campo de comentário...")
                    textarea_selectors = [
                        "textarea.bg-[#2a2a3b]",  # Seletor exato do textarea
                        "textarea#text",  # Usando o ID
                        "textarea[placeholder='comment']",  # Usando o placeholder
                        "[data-sentry-element='CommentTextArea']",  # Seletor original como fallback
                    ]

                    textarea = None
                    for selector in textarea_selectors:
                        try:
                            textarea = self.short_wait.until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                            )
                            if textarea:
                                break
                        except:
                            continue

                    if not textarea:
                        logger.error("Textarea não encontrado após tentar todos os seletores")
                        retry_count += 1
                        continue

                    try:
                        # Primeiro limpa qualquer texto existente
                        self.driver.execute_script("arguments[0].value = '';", textarea)
                        # Insere o texto usando send_keys para garantir que os eventos sejam disparados
                        textarea.send_keys(comment_text)
                        # Dispara eventos adicionais para garantir que o React detecte a mudança
                        self.driver.execute_script("""
                            let element = arguments[0];
                            element.dispatchEvent(new Event('input', { bubbles: true }));
                            element.dispatchEvent(new Event('change', { bubbles: true }));
                            element.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
                        """, textarea)
                        logger.info("Texto inserido no campo de comentário")
                        time.sleep(0.5)  # Pequena espera para o botão ser habilitado
                    except Exception as e:
                        logger.error(f"Erro ao inserir texto no textarea: {str(e)}")
                        retry_count += 1
                        continue

                    time.sleep(0.2)
                    
                    # Clicar no botão "Post Reply" imediatamente com JavaScript
                    logger.info("Procurando botão 'Post Reply'...")
                    post_button_selectors = [
                        "button.bg-green-400",  # Usando a classe específica
                        "button.hover\\:bg-green-200",  # Usando a hover state class
                        "button:contains('post reply')",  # Usando o texto do botão
                        "button[data-sentry-element='PostReplyButton']"  # Seletor original como fallback
                    ]

                    post_button = None
                    for selector in post_button_selectors:
                        try:
                            # Tenta encontrar usando JavaScript primeiro (mais rápido)
                            js_script = """
                                let buttons = document.querySelectorAll('button');
                                return Array.from(buttons).find(btn => 
                                    btn.textContent.toLowerCase().includes('post reply') &&
                                    !btn.disabled
                                );
                            """
                            post_button = self.driver.execute_script(js_script)
                            if post_button:
                                break
                        except:
                            continue

                    if not post_button:
                        logger.error("Botão 'Post Reply' não encontrado ou está desabilitado")
                        retry_count += 1
                        continue

                    try:
                        # Tenta clicar usando diferentes métodos
                        try:
                            # Primeiro tenta scroll até o botão
                            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", post_button)
                            time.sleep(0.1)
                            
                            # Tenta clicar com JavaScript
                            self.driver.execute_script("""
                                arguments[0].click();
                                arguments[0].dispatchEvent(new Event('click'));
                                arguments[0].form && arguments[0].form.submit();
                            """, post_button)
                            logger.info("Comentário enviado!")
                            return True
                            
                        except Exception as e:
                            logger.error(f"Erro ao clicar no botão post com JavaScript: {str(e)}")
                            # Tenta clicar normalmente como fallback
                            post_button.click()
                            logger.info("Comentário enviado (clique normal)!")
                            return True
                            
                    except Exception as e:
                        logger.error(f"Erro ao clicar no botão post: {str(e)}")
                        retry_count += 1
                        continue
                    
                except Exception as e:
                    logger.error(f"Erro ao postar comentário (tentativa {retry_count + 1}/{max_retries}): {str(e)}")
                    retry_count += 1
                    if retry_count < max_retries:
                        time.sleep(0.2)  # Espera mínima entre tentativas
                        continue
                    return False
            
            return False
            
        except Exception as e:
            logger.error(f"Erro crítico ao postar comentário: {str(e)}")
            return False

    def close(self):
        """Fecha o navegador"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Navegador fechado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao fechar o navegador: {str(e)}")

    def __del__(self):
        """Destrutor da classe"""
        self.close()