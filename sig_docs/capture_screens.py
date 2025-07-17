
#!/usr/bin/env python3
"""
Script para capturar pantallas de la aplicación SIG usando Playwright
"""
import asyncio
import os
import sys
from playwright.async_api import async_playwright
import time

async def capture_screenshots():
    """Captura pantallas de la aplicación SIG"""
    async with async_playwright() as p:
        # Lanzar navegador
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Ir a la aplicación (asumiendo que está corriendo en localhost:8000)
            await page.goto('http://localhost:8000', timeout=10000)
            await page.wait_for_timeout(2000)
            
            # Captura 1: Pantalla principal
            await page.screenshot(path='/home/ubuntu/sig_docs/img/pantalla_principal.png', full_page=True)
            print("✓ Capturada pantalla principal")
            
            # Intentar navegar por diferentes secciones si existen
            try:
                # Buscar botones o enlaces de navegación
                buttons = await page.query_selector_all('button, a, .menu-item')
                if len(buttons) > 1:
                    await buttons[1].click()
                    await page.wait_for_timeout(1000)
                    await page.screenshot(path='/home/ubuntu/sig_docs/img/funcionalidad_1.png', full_page=True)
                    print("✓ Capturada funcionalidad 1")
                
                if len(buttons) > 2:
                    await buttons[2].click()
                    await page.wait_for_timeout(1000)
                    await page.screenshot(path='/home/ubuntu/sig_docs/img/funcionalidad_2.png', full_page=True)
                    print("✓ Capturada funcionalidad 2")
                    
            except Exception as e:
                print(f"⚠ No se pudieron capturar funcionalidades adicionales: {e}")
            
        except Exception as e:
            print(f"❌ Error capturando pantallas: {e}")
            # Crear imagen placeholder si falla
            await page.set_content('<html><body><h1>Aplicación SIG Unificada</h1><p>Interfaz no disponible para captura</p></body></html>')
            await page.screenshot(path='/home/ubuntu/sig_docs/img/pantalla_principal.png')
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_screenshots())
