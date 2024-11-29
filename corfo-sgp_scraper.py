import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

def get_soup(url, session, data=None):
    if data:
        response = session.post(url, data=data)
    else:
        response = session.get(url)
    response.raise_for_status()
    return BeautifulSoup(response.text, 'html.parser')

def extract_project_data(row):
    data = {}
    data['CÓDIGO'] = row.find('span', class_='icono_bullet_busqueda').text.split()[1]
    data['DESCRIPCIÓN'] = row.find('div', style='border:solid 0px gainsboro; height:100px; width:580px; padding-left:10px; white-space:normal !important;').text.strip()
    
    details = row.find_all('td', colspan='5')
    data['NOMBRE'] = details[0].text.strip()
    data['LÍNEA'] = details[1].text.strip()
    data['BENEFICIARIO'] = details[2].text.strip()
    
    # Extracting region and impact details
    region_details = row.find_all('td', valign='top')
    data['REGIÓN'] = region_details[0].text.strip() if len(region_details) > 0 else ''
    data['IMPACTO'] = region_details[1].text.strip() if len(region_details) > 1 else ''
    
    # Extracting sector and duration details
    sector = row.find('th', text='Sector Económico:').find_next_sibling('td')
    data['SECTOR'] = sector.text.strip() if sector else ''
    
    duration = row.find('th', text='Duración (meses):').find_next_sibling('td')
    data['DURACIÓN'] = duration.text.strip() if duration else ''
    
    # Extracting financial details
    aporte_corfo = row.find('th', text='Aporte CORFO :').find_next_sibling('td')
    data['APORTE-CORFO'] = aporte_corfo.text.strip() if aporte_corfo else ''
    
    total = row.find('th', text='Total Proyecto:').find_next_sibling('td').find('div')
    data['TOTAL'] = total.text.strip() if total else ''
    
    # Extracting resolution details
    res = row.find('th', text='Número Resolución:').find_next_sibling('td')
    data['RES'] = res.text.strip() if res else ''
    
    fecha = row.find('th', text='Fecha Resolución:').find_next_sibling('td').find('div')
    data['FECHA'] = fecha.text.strip() if fecha else ''
    
    toma_razon = row.find('th', text='Fecha toma de Razón:').find_next_sibling('td').find('div')
    data['TOMA-RAZÓN'] = toma_razon.text.strip() if toma_razon else ''
    
    return data

def main():
    url = 'https://sgp.corfo.cl/sgp/publico/busqueda_proyectos.aspx'
    session = requests.Session()
    soup = get_soup(url, session)

    # Click on "Más" to open advanced filter
    viewstate = soup.find('input', {'name': '__VIEWSTATE'})['value']
    eventvalidation = soup.find('input', {'name': '__EVENTVALIDATION'})['value']
    data = {
        '__VIEWSTATE': viewstate,
        '__EVENTVALIDATION': eventvalidation,
        '__EVENTTARGET': 'ctl00$cphFiltro$lnkMas',
        '__EVENTARGUMENT': ''
    }
    soup = get_soup(url, session, data)

    # Select "FINALIZADO" in Estado Proyecto
    viewstate = soup.find('input', {'name': '__VIEWSTATE'})['value']
    eventvalidation = soup.find('input', {'name': '__EVENTVALIDATION'})['value']
    data = {
        '__VIEWSTATE': viewstate,
        '__EVENTVALIDATION': eventvalidation,
        'ctl00$cphFiltro$cboEstadoProyecto': '30',
        'ctl00$cphFiltro$btnFiltroAvanzado': 'Aplicar filtro'
    }
    soup = get_soup(url, session, data)

    projects = []
    while True:
        rows = soup.find_all('tr', class_=['GridRow_Default', 'GridAltRow_Default'])
        for row in rows:
            project_data = extract_project_data(row)
            projects.append(project_data)

        # Save to CSV
        df = pd.DataFrame(projects)
        df.to_csv('proyectos_corfo.csv', index=False)

        # Check for next page
        next_page = soup.find('input', {'title': 'Siguiente', 'class': 'rgPageNext'})
        if not next_page:
            break

        viewstate = soup.find('input', {'name': '__VIEWSTATE'})['value']
        eventvalidation = soup.find('input', {'name': '__EVENTVALIDATION'})['value']
        data = {
            '__VIEWSTATE': viewstate,
            '__EVENTVALIDATION': eventvalidation,
            '__EVENTTARGET': next_page['name'],
            '__EVENTARGUMENT': ''
        }
        soup = get_soup(url, session, data)
        time.sleep(2)  # Wait for the page to load

if __name__ == '__main__':
    main()