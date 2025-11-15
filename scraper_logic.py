# scraper_logic.py (VERSIUNEA 42.0 - DEBUG URL GENERATOR)

import os
import re 
from collections import defaultdict 
from typing import Optional, Dict, Any, List

# ------------------------------------------------------------------------------
# ⚙️ CONFIGURARE
# ------------------------------------------------------------------------------
# Template-uri pentru URL-uri specifice liniei
BASE_URL_TEMPLATE = "https://www.oddsportal.com/basketball/usa/nba/{match_slug}/#over-under;1;{line_value:.2f};0"
BASE_URL_AH_TEMPLATE = "https://www.oddsportal.com/basketball/usa/nba/{match_slug}/#ah;1;{line_value:.2f};0"
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# 🛠️ FUNCȚII AJUTĂTOARE (Păstrăm doar cele necesare)
# ------------------------------------------------------------------------------

def get_match_slug(url: str) -> Optional[str]:
    """Extrage slug-ul meciului (ex: phoenix-suns-indiana-pacers-KtP8YyZj) din URL-ul de bază."""
    # Pattern care caută slug-ul dintre ultima secțiune de director și #
    match = re.search(r'/[^/]+/[^/]+/([^/]+)/#', url)
    if match:
        return match.group(1)
    return None


# ------------------------------------------------------------------------------
# 🚀 FUNCȚIA PRINCIPALĂ DE DEBUG
# ------------------------------------------------------------------------------

def scrape_basketball_match_full_data_filtered(ou_link: str, ah_link: str) -> Dict[str, Any]:
    
    results: Dict[str, Any] = defaultdict(dict)
    
    # ----------------------------------------------------
    # PAS 1: Extragerea slug-ului
    # ----------------------------------------------------
    match_slug = get_match_slug(ou_link)
    
    if not match_slug:
        results['Error'] = "Eroare: Nu s-a putut extrage slug-ul meciului din URL-ul O/U furnizat."
        return dict(results)
    
    results['Match_Slug'] = match_slug

    # ----------------------------------------------------
    # PAS 2: Simulare Linii extrase (Folosim liniile confirmate de tine)
    # ----------------------------------------------------
    # Linii Over/Under pe care le-ai furnizat
    simulated_ou_lines = [216.5, 217.5, 218.5, 219.5, 220.5]
    
    # Linii Asian Handicap (presupunem aceeași structură)
    simulated_ah_lines = [2.5, 3.5, 4.5] 

    # ----------------------------------------------------
    # PAS 3: Generarea URL-urilor Over/Under
    # ----------------------------------------------------
    generated_ou_urls: List[str] = []
    
    for line_value in simulated_ou_lines:
        # Folosim formatul .2f pentru a asigura că numerele au două zecimale, 
        # așa cum necesită structura Oddsportal
        new_url = BASE_URL_TEMPLATE.format(match_slug=match_slug, line_value=line_value)
        generated_ou_urls.append(new_url)
        
    results['Generated_OU_URLs'] = generated_ou_urls

    # ----------------------------------------------------
    # PAS 4: Generarea URL-urilor Asian Handicap
    # ----------------------------------------------------
    generated_ah_urls: List[str] = []
    
    for line_value in simulated_ah_lines:
        new_url = BASE_URL_AH_TEMPLATE.format(match_slug=match_slug, line_value=line_value)
        generated_ah_urls.append(new_url)
        
    results['Generated_AH_URLs'] = generated_ah_urls
            
    return dict(results)

# P.S.: Codul nu mai folosește Selenium/Chromedriver, deci nu necesită inițializare/închidere.
# Te rog să îmi dai rezultatul rulării acestui cod (V42.0)
