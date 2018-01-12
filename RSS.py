'''
References：
http://boto3.readthedocs.io/en/latest/index.html
https://pythonhosted.org/feedparser/index.html
https://qiita.com/shunsuke227ono/items/da52a290f78924c1f485
https://qiita.com/attakei/items/b3c955fff1bb05adb07b
https://qiita.com/Morio/items/7538a939cc441367070d
https://qiita.com/sokutou-metsu/items/5ba7531117224ee5e8af
https://dev.classmethod.jp/cloud/aws/upload-json-directry-to-s3-with-python-boto3/
https://dev.classmethod.jp/cloud/aws/generate-pre-signed-url-for-s3-with-boto3/
https://gist.github.com/hrouault/1358474
'''

import boto3
import feedparser
import html
import json
import pyperclip
import sys

from datetime import datetime


class StoringRSS:

	def __init__(self):
		print('---Connecting S3---')
		self.s3 = boto3.client('s3')
		self.bucket_name = 'Your bucket_name'
		print('---Conected S3---')

	def storing_feed(self):
		json_key = 'feed_%s.json' % datetime.now().strftime('%Y%m%d%H%M%S')
		data = {}

		print('---Parsing RSS---')
		url = 'https://dev.classmethod.jp/category/business/bigdata/feed/'
		feed = feedparser.parse(url)
		if feed.bozo == 1:
			print('---Parsing failed---')
			error = {'Error': str(feed.bozo_exception)}
			json_str = json.dumps(error, ensure_ascii=False)
			res_err = self.s3.put_object(Body=json_str, Bucket=self.bucket_name, Key=json_key)
			print('Error: ', feed.bozo_exception)
			return 0
		print('---Parsed RSS---')

		for entry in range(len(feed.entries)):
			key = 'article' + str(entry+1)
			article = {
				key: {
					'Title': feed.entries[entry].title,
					'Author': feed.entries[entry].author,
					'Discription': html.unescape(feed.entries[entry].summary)
				}
			}
			data.update(article)
		json_str = json.dumps(data, ensure_ascii=False)
		res_put = self.s3.put_object(Body=json_str, Bucket=self.bucket_name, Key=json_key)
		print('---Uploded %s to S3---' % json_key)
		return 0

	def generate_url(self):

		print('---Displaying 10 new objects---')
		res_list = self.s3.list_objects_v2(Bucket=self.bucket_name)
		keys = []
		try:
			for obj in res_list['Contents']:
				keys.append(obj['Key'])
		except KeyError:
			print('---Bucket %s is empty---' % self.bucket_name)
			return 0
		keys.sort()
		keys.reverse()
		cnt = 0
		valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
		for key in keys:
			print(key)
			cnt += 1
			if cnt % 10 == 0:
				while True:
					choice = input('Will you display next 10 objects？[Y/n]: ').lower()
					if choice in valid:
						break
					else:
						print('Please respond with "yes" or "no" (or "y" or "n").')
						continue
				if valid[choice] is True:
					continue
				else:
					break

		while True:
			issue = input('Please Enter the name of an object which you want to creates pre-signed URL of: ')
			if issue in keys:
				break
			else:
				print('Please respond with an existing key.')
				continue

		presigned_url = self.s3.generate_presigned_url(
			ClientMethod='get_object',
			Params={'Bucket': self.bucket_name, 'Key': issue},
			ExpiresIn=3600,
			HttpMethod='GET'
		)
		print('---Created pre-signed URL---')
		print('URL: ', presigned_url)
		pyperclip.copy(presigned_url)
		print('---Copied URL to the clipboard---')
		return 0


if __name__ == '__main__':
	StoringRSS = StoringRSS()
	error_message = 'Please give an argument from two below.\n'\
					'storing_feed: Store RSS feed to S3 as json.\n'\
					'generate_url: Create pre-signed url of an object.'\

	try:
		arg = sys.argv[1]
	except IndexError:
		print(error_message)
	else:
		if arg == 'storing_feed':
			StoringRSS.storing_feed()
		elif arg == 'generate_url':
			StoringRSS.generate_url()
		else:
			print(error_message)
