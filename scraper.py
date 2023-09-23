import requests
from bs4 import BeautifulSoup
import csv
import time
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import re
import configparser
import logging
import sys
import traceback  # Import du module traceback


logging.basicConfig(filename='errors.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
console = logging.StreamHandler()
logger.addHandler(console)


# Get the directory containing your packed program's executable
#base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
config_path = os.path.join(base_path, 'config.ini')
last_articles_file = os.path.join(base_path, 'last_articles.csv')
articles_file = os.path.join(base_path, 'articles.csv')
print("path: "+config_path)
# Charger le fichier de configuration
config = configparser.ConfigParser()

config.read(config_path)

# Accéder aux paramètres

ANIBIS_URL = config['DEFAULT']['ANIBIS_URL']
GMAIL_ADDRESS = config['DEFAULT']['GMAIL_ADDRESS']
GMAIL_APP_PASSWORD = config['DEFAULT']['GMAIL_APP_PASSWORD']
INTERVAL = int(config['DEFAULT']['INTERVAL'])
NEW_ARTICLES_NOTIF = bool(config['DEFAULT']['NEW_ARTICLES_NOTIF'])

INTERVAL_RANDOMIZE= 400

# Vos identifiants Gmail
# Vos identifiants Gmail

def convert_chf_to_number(chf_string):
    # Supprimer le préfixe "CHF "
    try:
        cleaned_string = chf_string.replace("CHF ", "")
    
        # Supprimer tous les caractères non numériques, sauf le point décimal
        number_string = ''.join(char for char in cleaned_string if char.isdigit() or char == ".")
        
        # Convertir la chaîne en un nombre
        return float(number_string)
    except:
        return 0


# Fonction pour envoyer un e-mail formaté
def send_email(subject, content, isFirstNotif):
    msg = MIMEMultipart("alternative")
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = GMAIL_ADDRESS  # ou toute autre adresse e-mail à laquelle vous souhaitez envoyer
    #msg["To"] = ", ".join(recipients_list)  
    msg["Subject"] = subject
    
    content_style = """
                table {
                width: 80%;
                border-collapse: collapse;
                margin: 50px 0;
                font-size: 18px;
                text-align: left;
            }
            th, td {
                padding: 10px;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #f2f2f2;
            }
            tr:hover {
                background-color: #f5f5f5;
            }
    """

    # Créer le contenu HTML de l'e-mail
    if isFirstNotif:
        html_content = f"""
        <html>
        <body>
            <h2>Notification du scrapper</h2>
            {content}
        </body>
        </html>
        """
    else:
        html_content = f"""

        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Voitures</title>
            <style>
                {content_style}
            </style>
        </head>
        <body>
            <h2>Notification du scrapper</h2>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Titre</th>
                    <th>Prix</th>
                    <th>Lien</th>
                    <th>Km</th>
                    <th>Annee</th>
                    <th>Lieu</th>
                </tr>
            </thead>
            <tbody>
            {content}
            </tbody>
        </table>
        """
    msg.attach(MIMEText(html_content, "html"))
    try:
        # Envoyer l'e-mail
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        print(f'Notification sent to email :"{GMAIL_ADDRESS}"')
    except:
        print(f'Cannot send email to :"{GMAIL_ADDRESS}"')
        print("Exception Traceback:")
        traceback.print_exc()  # Imprime la trace de la pile


def getSoup (url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(url, headers=headers)
        # Handle potential HTTP errors
    try:
        response.raise_for_status()  # Raises stored HTTPError, if one occurred.
    except requests.HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')  # e.g. 404 or 500
        return None
    except Exception as err:
        print(f'Other error occurred: {err}')
        return None

    # Step 2: Parse the content using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup

# Charger le contenu d'un fichier CSV dans un dictionnaire
def load_csv_to_dict(filename):
    data_dict = {}
    with open(filename, 'r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=';')
        next(reader)  # Ignorer l'en-tête
        for row in reader:
            title = row[0]
            price = row[1]
            link = row[2]
            id = row[3]
            data_dict[id] = (title, price, link)
    return data_dict

send_email("Scrapper Starting", "<p>Scrapping starting now and will send you notification when price are dropping</p> <p>INTERVAL is set to "+str(INTERVAL)+" second, with more or less "+str(INTERVAL_RANDOMIZE)+" sec</p>", True)

while True: 
    try:
        #url_base = "https://www.anibis.ch/fr/c/automobiles-voitures-de-tourisme?ae=1&aral=832_0_145000%2C833_2014_"
        url_base = ANIBIS_URL
        url = url_base
        sleeptime = 3600
        # Step 1: Fetch the webpage content
        page = 1
        hasNextPage = True
        soup = getSoup(url)
        # Extraction des données


        # Liste pour stocker les données extraites
        data_list = []
        email_content = ""

        while hasNextPage:
            print('checking page ' + str(page) + '... url: ' + url)
            articles = soup.find_all('article')
            nextButton = soup.find_all('div', class_='sc-1d4mdus-0 eMiYgt')

            # Boucle sur chaque article pour extraire les données
            for article in articles:
                title = article.find('div', class_='lwk7wa-0 bVsXyN').text.strip() if article.find('div', class_='lwk7wa-0 bVsXyN')else None
                price = article.find('div', class_='sc-1holcpr-0 leZeeB').text.strip() if article.find('div', class_='sc-1holcpr-0 leZeeB') else None
                link = article.find('a', class_='sc-1yo7ctu-0 bRDNul')['href'] if article.find('a', class_='sc-1yo7ctu-0 bRDNul') else None
                details = article.find('div', class_='yd8154-0 jLDIPt').text.strip() if article.find('div', class_='yd8154-0 jLDIPt') else None
                location = article.find('div', class_='sc-114vkp9-0 wzCeg').text.strip() if article.find('div', class_='sc-114vkp9-0 wzCeg') else None
                id = article['id'].split('card_')[1]
                
                details_withoutapostrphe = details.replace("'","")
                years = details_withoutapostrphe.split(" ")[0]
                kilometers = details_withoutapostrphe.split(" ")[2]

                data_list.append([title, price, 'https://anibis.ch'+link, id, years, kilometers, location])

            if len(nextButton) < 1 :
                print("il y n'y a pas de page suivante")
                hasNextPage = False
                        # Enregistrement des données dans un fichier CSV
                print("ouverture du fichier: "+articles_file)
                with open(articles_file, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file, delimiter=';')
                    writer.writerow(["Title", "Price", "Link", "Id", "Year", "Km", "Location"])  # En-tête du CSV
                    writer.writerows(data_list)
            else:
                page = page + 1
                # Concatenate url and page as a string 
                url = url_base + '&pi=' + str(page)
                retries = 3
                while (retries > 0):
                    soup = getSoup(url)
                    if soup is None:
                        retries = retries - 1
                        time.sleep(random.randint(2, 6))
                    else:
                        break

                time.sleep(random.randint(2, 6))
        # Vérifier si le fichier 'last_articles.csv' existe
        print("test si fichier: "+last_articles_file+" existe")
        if os.path.exists(last_articles_file):

            # Charger les deux fichiers CSV
            print("lecture fichier "+last_articles_file)
            first_csv = load_csv_to_dict(last_articles_file)
            print("lecture fichier "+articles_file)
            second_csv = load_csv_to_dict(articles_file)

            # Comparer les deux dictionnaires
            for id, (title, price, link) in second_csv.items():
                if id in first_csv:
                    first_title, first_price, first_link = first_csv[id]
                    if first_price != price:
                        first_price_nbr = convert_chf_to_number(first_price)
                        price_nbr = convert_chf_to_number(price)
                        if(price_nbr < first_price_nbr) :
                            print(f'ID: "{id}" Le prix de "{title}" a changé de {first_price} à {price}. Lien: {link}')
                            #email_content += f'<p>ID: "{id}" Le prix de "{title}" a changé de "{first_price}", à {price} <a href="{link}">Lien</a></p>'
                            email_content += f'<tr> <td>{id}</td><td>{title} </td> <td> {first_price_nbr} CHF --> {price}</td>  <td><a href="{link}">Lien</a></td><td>{kilometers}</td><td>{years}</td><td>{location}</td></tr>'
                elif NEW_ARTICLES_NOTIF:
                    print(f'ID: "{id}" Nouvel élément trouvé dans le second CSV: "{title}" avec le prix {price}. Lien: {link}')
                    #email_content += f'<p>ID: "{id}" Nouvel élément trouvé : "{title}" avec le prix "{price}" <a href="{link}">Lien</a></p>'
                    
        else:
            print("Le fichier 'last_articles.csv' n'existe pas, je le créer")

        #current articles become las_articles
        os.rename(articles_file, last_articles_file)

        if email_content != "":
            send_email("Scrapper Notification", email_content, False)


        
        sleeptime = random.randint(INTERVAL-INTERVAL_RANDOMIZE, INTERVAL+INTERVAL_RANDOMIZE)
        print("waiting "+ str(sleeptime) + " seconds before new scrap...")
        time.sleep(sleeptime)
        # Extraction des données
        #articles = soup.find_all('article')
        #items = articles.find_all('div', class_='lwk7wa-0 bVsXyN')
        #prices = articles.find_all('div', class_='sc-1holcpr-0 leZeeB')

        # Préparation des données pour le CSV
        #data = []
        #for item, price in zip(items, prices):
        #    data.append([item.text.strip(), price.text.strip()])

        # Enregistrement dans un fichier CSV
        #with open('articles.csv', 'w', newline='', encoding='utf-8') as file:
        #    writer = csv.writer(file)
        #    writer.writerow(['Article', 'Prix'])  # En-tête du CSV
        #    writer.writerows(data)
    except Exception as e:
        logging.error(f"Une erreur s'est produite : {e}")
        print(f"Une erreur s'est produite : {e}")
