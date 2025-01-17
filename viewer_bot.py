import asyncio
import aiohttp
from typing import List
import sys
import logging
from datetime import datetime
import random
import brotli  # Brotli desteği için

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ViewerBot:
    def __init__(self, yayin_url: str, izleyici_sayisi: int, bekleme_suresi: float = 30):
        self.yayin_url = yayin_url
        self.izleyici_sayisi = izleyici_sayisi
        self.bekleme_suresi = bekleme_suresi
        self.aktif_oturumlar: List[aiohttp.ClientSession] = []
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Edge/120.0.0.0'
        ]
        
    async def iframe_istegi_olustur(self, oturum_id: int):
        try:
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'tr,en-US;q=0.7,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate',  # br kaldırıldı
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'iframe',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'cross-site',
                'Pragma': 'no-cache',
                'Cache-Control': 'no-cache',
                'DNT': '1',
                'Sec-GPC': '1'
            }
            
            async with aiohttp.ClientSession(headers=headers) as oturum:
                self.aktif_oturumlar.append(oturum)
                while True:
                    try:
                        async with oturum.get(self.yayin_url, allow_redirects=True, timeout=30) as yanit:
                            if yanit.status == 200:
                                logger.info(f"İframe {oturum_id}: Bağlantı başarılı ✓ [HTTP {yanit.status}]")
                                await yanit.read()
                            else:
                                logger.warning(f"İframe {oturum_id}: Bağlantı hatası ✗ [HTTP {yanit.status}]")
                    except asyncio.TimeoutError:
                        logger.error(f"İframe {oturum_id}: Zaman aşımı hatası")
                    except Exception as hata:
                        logger.error(f"İframe {oturum_id} hatası: {str(hata)}")
                    
                    bekleme = self.bekleme_suresi + random.uniform(-2, 2)
                    await asyncio.sleep(max(1, bekleme))
                    
        except Exception as hata:
            logger.error(f"İframe {oturum_id} oturum hatası: {str(hata)}")
        finally:
            if oturum in self.aktif_oturumlar:
                self.aktif_oturumlar.remove(oturum)

    async def baslat(self):
        print(f"\n{'='*50}")
        print(f"Bot başlatılıyor - Hedef: {self.izleyici_sayisi} iframe")
        print(f"URL: {self.yayin_url}")
        print(f"{'='*50}\n")
        
        gorevler = []
        for i in range(self.izleyici_sayisi):
            gorev = asyncio.create_task(self.iframe_istegi_olustur(i + 1))
            gorevler.append(gorev)
        
        try:
            await asyncio.gather(*gorevler)
        except KeyboardInterrupt:
            print("\nBot durduruluyor...")
            for oturum in self.aktif_oturumlar:
                await oturum.close()
            sys.exit(0)

def kullanici_bilgilerini_al():
    print("\n=== Yayın İzleyici Botu ===\n")
    
    # Platform seçimi
    while True:
        print("\nHangi platform için izleyici oluşturulacak?")
        print("1. Kick")
        print("2. Twitch")
        platform = input("\nSeçiminiz (1/2): ").strip()
        if platform in ['1', '2']:
            break
        print("Lütfen geçerli bir platform seçin!")
    
    # Yayıncı adı
    while True:
        yayinci = input("\nYayıncı adını girin: ").strip()
        if yayinci:
            break
        print("Yayıncı adı boş olamaz!")
    
    # URL oluşturma
    if platform == "1":
        yayin_url = f"https://kick.com/embed/{yayinci}"
    else:
        yayin_url = f"https://player.twitch.tv/?channel={yayinci}&parent=twitch.tv"
    
    # İframe sayısı
    while True:
        try:
            izleyici = int(input("\nKaç iframe oluşturulsun?: ").strip())
            if 0 < izleyici <= 999:
                break
            print("Lütfen 1-999 arası bir sayı girin!")
        except ValueError:
            print("Lütfen geçerli bir sayı girin!")
    
    # Bekleme süresi
    while True:
        try:
            sure = float(input("\nHer bağlantı arasında kaç saniye beklensin? (Önerilen: 30): ").strip() or "30")
            if sure > 0:
                break
            print("Lütfen 0'dan büyük bir sayı girin!")
        except ValueError:
            print("Lütfen geçerli bir sayı girin!")
    
    return yayin_url, izleyici, sure

def main():
    try:
        # Brotli kurulu mu kontrol et
        try:
            import brotli
        except ImportError:
            print("\nBrotli kütüphanesi eksik. Yükleniyor...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "Brotli"])
            print("Brotli kurulumu tamamlandı.\n")
        
        yayin_url, izleyici_sayisi, bekleme_suresi = kullanici_bilgilerini_al()
        
        bot = ViewerBot(
            yayin_url=yayin_url,
            izleyici_sayisi=izleyici_sayisi,
            bekleme_suresi=bekleme_suresi
        )
        
        print("\nBotu durdurmak için Ctrl+C tuşlarına basın...")
        asyncio.run(bot.baslat())
        
    except KeyboardInterrupt:
        print("\nProgram sonlandırılıyor...")
        sys.exit(0)

if __name__ == "__main__":
    main() 
