import requests
from bs4 import BeautifulSoup
import pandas as pd
import os, shutil
import gspread
from datetime import datetime

def saveMainPageInFile(url):
    try:
        f = open(f'index.html', 'w', encoding='utf-8')
        res = requests.get(url)
        f.write(res.text)
        f.close()
    except:
        print('файл уже существует.')

def getLinkToNextPage(pagination_list):
    linkNextPage = pagination_list.find_all("li")
    if(linkNextPage[-1].find("a")):
        print('ЕСТЬ следующая страница')
        url = linkNextPage[-1].find("a").get("href")
        return(url)
    else:
        print('НЕТ следующей страницы')
        return False

def searchAllPages(next_page):
    n = 1
    next = next_page
    if os.path.exists('./pages/'):
        shutil.rmtree('./pages/')
    os.mkdir('./pages')

    while next:
        n += 1
        f = open(f'./pages/page{n}.html', 'w', encoding='utf-8')
        res = requests.get(next)
        f.write(res.text)
        f.close()
        print(f'Записан файл  - page{n}.html')
        soup = BeautifulSoup(res.text, 'html.parser')
        if(soup.find("ul", class_='page-numbers')):
            divPagination = soup.find("ul", class_='page-numbers')
            next = getLinkToNextPage(divPagination)
        else:
            next = False
    print(f'--- Количество записанных страниц - {n} ---')

def saveAllPagesWithProducts():
    with open("index.html") as fp:
        soup = BeautifulSoup(fp, 'html.parser')
    if(soup.find("ul", class_='page-numbers')):
        divPagination = soup.find("ul", class_='page-numbers')
        next = getLinkToNextPage(divPagination)
        searchAllPages(next)
    else:
        print('Это единственная страница. Пагинации нет.')

def findAllProductsOnPage(file_name):
    with open(file_name, encoding="utf-8") as fp:
        soup = BeautifulSoup(fp, 'html.parser')
    listProducts = soup.find(attrs='products')
    items = listProducts.find_all(class_=['product', 'type-product'])
    data = []
    for item in items:
        title = item.find("h2").text
        price = int(item.find("bdi").text.replace(',00\xa0₴', ''))
        link = item.find("a").get("href")
        data.append({
            "title": title,
            "price": price,
            "link": link
            })
    return data

def dataCollection():
    numFiles = len(os.listdir('./pages/'))
    data = []
    data = findAllProductsOnPage('index.html')
    print(len(data))
    for num in range(2, numFiles+2):
        fileName = f'./pages/page{num}.html'
        data = data + findAllProductsOnPage(fileName)
    dateNow = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    with open(f'./history/all_products_{dateNow}.txt', "w", encoding="utf-8") as fp:
        for item in data:
        # write each item on a new line
            fp.write("%s\n" % item)
    # record to spreadsheet
    # saveDataToSpreadsheet(data)

def compareDate():
    numFiles = len(os.listdir('./history/'))
    if numFiles < 2:
        print("В папке history нечего сравнивать. Мало файлов")
        return
    allFiles = os.listdir("history")
    list1 = []
    list2 = []
    with open(f'./history/{allFiles[-2]}', "r", encoding="utf-8") as f1, open(f'./history/{allFiles[-1]}', "r", encoding="utf-8") as f2:
        for line in f1:
            x = line[:-1]
            list1.append(eval(x))
        for line in f2:
            x = line[:-1]
            list2.append(eval(x))
    newData = []
    oldProduct = []
    for item1 in list1:
        for idx, item2 in enumerate(list2):
            if(item1["title"]==item2["title"]):
                if(item1["price"]!=item2["price"]):
                    newData.append(f'У товара \"{item2["title"]}\" изменилась цена. Была - {item1["price"]};Стала - {item2["price"]}')
                oldProduct.append(idx)
                break
            if(idx == len(list2)-1):
                print('I am last element')
                newData.append(f'А этот товар удален {item1["title"]}')
    n = 0
    for idx, item in enumerate(oldProduct):
        item = item - n
        if idx != item:
            newData.append(f'А этот товар был добавлен {list2[idx+n]["title"]}')
            n += 1
    print(newData)

# Запись даных в гугл таблицу для глубокого анализа.
# файл это доступ for-parse.json к указанной таблице
def saveDataToSpreadsheet(data):
    df = pd.DataFrame(data)
    dateNow = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    df['timestamp'] = dateNow
    gc = gspread.service_account(filename='for-parse.json')
    sh = gc.open("Parse").worksheet("lar")
    sh.update([df.columns.values.tolist()] + df.values.tolist())

url = 'https://larpradeda.com.ua/all-products-ua/'
# url = 'https://larpradeda.com.ua/product-category/pidvisy-ta-kulony/'
def main():
    saveMainPageInFile(url)
    saveAllPagesWithProducts()
    dataCollection()
    compareDate()


if __name__ == '__main__':
    main()
    # dataCollection()
    # compareDate()
    # os.remove('./pages/')
    # shutil.rmtree('./pages/')
    # os.rmdir('./pages/')