# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyleft (c) 2015-2099 宝塔软件(http://bt.cn) All lefts reserved.
# +-------------------------------------------------------------------
# | Author: linxiao
# +-------------------------------------------------------------------
# +--------------------------------------------------------------------
# |   宝塔网站监控报表定时任务
# +-------------------------------------------------------------------
from __future__ import absolute_import, print_function, division
import os
import sys

import json

os.chdir("/www/server/panel")
sys.path.insert(0, "/www/server/panel/class/")
sys.path.insert(0, "/www/server/panel")

import public
from crontab import crontab
import total_tools as tool

task_config = "/www/server/panel/plugin/total/task_config.json"

def get_config():
	try:
		return json.loads(public.readFile(task_config))	
	except:
		pass
	return {
		"task_id": -1,
		"task_list": ["record_log_size", "generate_report", "migrate_hot_logs"],
		"default_execute_hour": 3,
		"default_execute_minute": 10,
	}

def create_background_task():
	config = get_config()
	if "task_id" in config.keys() and config["task_id"] > 0:
		res = public.M("crontab").field("id, name").where("id=?", (config["task_id"],)).find()
		if res and res["id"] == config["task_id"]:
			# print("计划任务已存在。")
			print(tool.getMsg("SCHEDULED_TASK_EXISTS"))
			return True 

	# name = "[勿删]宝塔网站监控报表插件定时任务"
	name = tool.getMsg("SCHEDULED_TASK_NAME")
	c = crontab()
	get = public.dict_obj()
	get.type = "day"
	get.hour = config["default_execute_hour"]
	get.minute = config["default_execute_minute"]
	get.sBody = "nice -n 10 " + public.get_python_bin()+" /www/server/panel/plugin/total/total_task.py execute"
	get.sType = "toShell"
	get.name = name 
	get.sName = ""
	get.urladdress = ""
	get.backupTo = ""
	res = c.AddCrontab(get)
	if "id" in res.keys():
		config["task_id"] = res["id"]
		public.writeFile(task_config, json.dumps(config))
		return True
	
	return False

def remove_background_task():
	config = get_config()
	if "task_id" in config.keys() and config["task_id"] > 0:
		res = public.M("crontab").field("id, name").where("id=?", (config["task_id"],)).find()
		if res and res["id"] == config["task_id"]:
			c = crontab()
			get = public.dict_obj()
			get.id = res["id"]
			del_res = c.DelCrontab(get)
			if del_res and "status" in del_res.keys():
				if del_res["status"]:
					print(del_res["msg"])
					return True 
	return False

def record_log_size():
	pass

def execute():
	try:
		import time
		now = time.strftime("%Y-%m-%d", time.localtime())
		# print("[{}]网站监控报表插件定时执行以下任务：".format(now))
		print(tool.getMsg("TIPS_SCHEDULED_TASK", args=(now,)))
		# print("1. 生成数据周报和数据月报。此任务需要分析日志数据，会占用服务器计算资源，请选择在服务器闲时执行。")
		print(tool.getMsg("TIPS_SCHEDULED_TASK_1"))
		print(tool.getMsg("TIPS_SCHEDULED_TASK_2"))
		print(tool.getMsg("TIPS_SCHEDULED_TASK_3"))
		print(tool.getMsg("TIPS_SCHEDULED_TASK_NOTICE"))
		print("-"*30)
		config = get_config()	
		task_list = config["task_list"]
		for task in task_list:
			if task == "record_log_size":
				try:
					record_log_size()
				except:
					pass
			elif task == "generate_report":
				try:
					from total_report import automatic_generate_report 
					automatic_generate_report()
				except:
					pass
			elif task == "migrate_hot_logs":
				try:
					from total_migrate import total_migrate
					tm = total_migrate()
					tm.migrate_hot_logs("yesterday")
				except:
					pass
	except Exception as e:
		print(e)

if __name__ == "__main__":
	if len(sys.argv) > 1:
		action = sys.argv[1]
		if action == "execute":
			execute()
		elif action == "remove":
			remove_background_task()
	# print(get_config())
	# create_background_task()