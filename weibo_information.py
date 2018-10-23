from urllib.parse import urlencode
import requests
from pyquery import PyQuery as pq
from pymongo import MongoClient
base_url = 'https://m.weibo.cn/api/container/getIndex?'

headers = {
    'Host': 'm.weibo.cn',
    'Referer': 'https://m.weibo.cn/u/2830678474',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36 QIHU 360EE',
    'X-Requested-With': 'XMLHttpRequest'
}
client = MongoClient('mongodb://localhost:27017/')
db = client['weibo']
collection = db['weibo']


def get_page(page):
    params = {
        'type': 'uid',
        'value': '2830678474',
        'containerid': '1076032830678474',
        'page': page
    }
    url = base_url + urlencode(params)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except requests.ConnectionError as e:
        print('Error', e.args)


def parse_page(json):
    if json:
        items = json.get('data').get('cards')
        for item in items:
            item = item.get('mblog')
            weibo = {}
            try:
                weibo['id'] = item.get('id')
                weibo['text'] = pq(item.get('text')).text()
                weibo['attitudes'] = item.get('attitudes_count')
                weibo['comments'] = item.get('comments_count')
                weibo['reposts'] = item.get('reposts_count')
                yield weibo
            except AttributeError:
                pass


def save_to_mongo(result):
    # 根据id这个属性，查找数据库所有数据的ID，返回的是字典。
    # 将要返回的值设为1.
    exit_ids = collection.find({}, {"_id": 0, "id": 1})
    # 将MngoDB中存在的数据，根据ID存储在一个集合List里，与将要存储的数据ID进行比较，实现去重。
    List = set()
    for exit_id in exit_ids:
        for value in exit_id.values():
            List.add(value)
    if result['id'] not in List:
        collection.insert(result)
        print("Save to mongodb!")
    else:
        print(result['id'] + " is exit Mongodb!")


if __name__ == '__main__':
    for page in range(1, 5):
        num = 0
        json = get_page(page)
        results = parse_page(json)
        for result in results:
            save_to_mongo(result)
