from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
import re 
import json
import os 
import requests

new_data = {}
new_ads = []

XPATHES = {"title":'//*[@id="content-container-root"]/div[2]/div[1]/div/h1'
	,"price":'//*[@id="content-container-root"]/div[2]/div[2]/div[2]/div[1]/div[1]/div[1]/div[1]/h2',
	"mileage":'//*[@class="itemval"][contains(text(),"km")]',
	"color":'//*[@class="sc-font-bold"][contains(text(),"Farbe")]/following-sibling::div',
	"power":'//*[@class="sc-font-bold"][contains(text(),"Leistung")]/following-sibling::div'}

URL_PART= "https://www.truckscout24.de/transporter/gebraucht/kuehl-iso-frischdienst/renault?currentpage=" #link without page number
CURRENT_DIR  = os.getcwd()
DATA_DIR = os.path.join(CURRENT_DIR,"data")
JSON_DIR = os.path.join(DATA_DIR,"data.json")
	
options = Options()
options.add_argument("--headless")
options.add_argument('--ignore-certificate-errors')
	
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def process(ad):
	ad["price"] = re.sub(r'[^0-9]+', "", ad["price"]) #data processing
	if ad["price"]:
		ad["price"] = int(ad["price"].strip(',-'))
	else:
		ad["price"] = 0
	if ad["mileage"] != 0:
		ad["mileage"] = re.sub(r'[^0-9.]+', "" ,ad["mileage"])
		ad["mileage"] = int(float(ad["mileage"].strip()))
	if ad["power"] != 0:
		ad["power"] = int(ad["power"][:ad["power"].find('k')].strip())


def get_by_xpath(name,xpath,ad): #return the text of the element by xpath
	try:
		elem=driver.find_element(By.XPATH,xpath).get_attribute('innerText')
	except NoSuchElementException:
		if isinstance(ad[name], str):
			return ""
		return 0
	return elem

def get_description():
	description = ""
	raw_description = driver.find_elements(By.CSS_SELECTOR,'[data-type="description"]') #raw list of description elements
	if raw_description:
		for paragraph in raw_description: #\xa0\n
			paragraph = paragraph.get_attribute("innerText")
			description += paragraph
	description = description.replace('\xa0\n', ' ')
	description = description.removesuffix('\xa0')
	return description

def download_images(ad):
	image_dir = os.path.join(DATA_DIR,str(ad["id"]))
	if not os.path.exists(image_dir):
		os.mkdir(image_dir)
		images = []
		for i in range(1,4): #get src of first 3 images
			images.append(driver.find_element(By.XPATH,f'//*[@id="detpics"]/as24-pictures/div/div[2]/div/as24-carousel[1]/div[1]/div[{i}]/div/img'))
		num = 1
		for image in images: # download images
			image_src = image.get_attribute("data-src")
			response = requests.get(image_src)
			if response.status_code == 200:
				with open(os.path.join(image_dir,"image"+str(num)+".jpg"), 'wb') as f:
					f.write(response.content)
			num += 1

def dump_data():
	new_data["ads"] = new_ads
	if os.path.exists(JSON_DIR):
		with open(JSON_DIR,"r") as file:
			data = json.load(file)
			data.update(new_data)
		with open(JSON_DIR,"w") as file:
			json.dump(data,file)
	else:
		with open(JSON_DIR,"w") as file:
			json.dump(new_data,file)



def main(start_page=1,end_page=4):
	if not os.path.exists(DATA_DIR):
		os.mkdir(DATA_DIR)
	for i in range (start_page,end_page+1):
		ad = {"id":i,"href":"","title":"","price":0,"mileage":0,"color":"","power":0,"description":""} #empty initial ad
		driver.get(URL_PART+str(i)) #link + page number
		item = driver.find_element(By.XPATH,'//*[@class="ls-titles"]/a') #first ad on the page
		href = item.get_attribute('href')
		driver.get(href)
		ad["href"] = href
		ad["description"] = get_description()
		for name,xpath in XPATHES.items():
			ad[name] = get_by_xpath(name,xpath,ad)
		process(ad)
		download_images(ad)
		new_ads.append(ad)
	dump_data()
	driver.close()

if __name__ == '__main__':
	main()
