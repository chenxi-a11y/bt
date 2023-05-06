# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyleft (c) 2015-2099 宝塔软件(http://bt.cn) All lefts reserved.
# +-------------------------------------------------------------------
# | Author: linxiao
# +-------------------------------------------------------------------
# +--------------------------------------------------------------------
# |   宝塔网站监控报表工具函数
# +--------------------------------------------------------------------
from __future__ import absolute_import, print_function, division
import os
import sys
import time
import json

os.chdir("/www/server/panel")
sys.path.insert(0, "/www/server/panel/class")

import public
__frontend_path = '/www/server/panel/plugin/total'
__backend_path = "/www/server/total"

def getMsg(msg, args=[]):
    language_file = 'total.json'
    lang_file = os.path.join(__frontend_path, 'language',  public.GetLanguage(), language_file)
    log_message = json.loads(public.readFile(lang_file))
    keys = log_message.keys()
    if type(msg) == str:
        if msg in keys:
            msg = log_message[msg]
            for i in range(len(args)):
                rep = '{'+str(i+1)+'}'
                msg = msg.replace(rep,str(args[i]))
    return msg

def returnMsg(status, msg, args=[]):
    """
        @name 取通用dict返回
        @author hwliang<hwl@bt.cn>
        @param status  返回状态
        @param msg  返回消息
        @return dict  {"status":bool,"msg":string}
    """
    msg = getMsg(msg, args) 
    return {'status':status,'msg':msg} 

def get_time_key(date=None):
    if date is None:
        date = time.localtime()
    time_key = 0
    time_key_format = "%Y%m%d%H"
    if type(date) == time.struct_time:
        time_key = int(time.strftime(time_key_format, date))
    if type(date) == str:
        time_key = int(time.strptime(date, time_key_format))
    return time_key

def get_time_interval(local_time):
    start = None
    end = None
    time_key_format = "%Y%m%d00"
    start = int(time.strftime(time_key_format, local_time))
    time_key_format = "%Y%m%d23"
    end = int(time.strftime(time_key_format, local_time))
    return start, end

def get_timestamp_interval(local_time):
    start = None
    end = None
    start = time.mktime((local_time.tm_year, local_time.tm_mon,
                         local_time.tm_mday, 0, 0, 0, 0, 0, 0))
    end = time.mktime((local_time.tm_year, local_time.tm_mon,
                       local_time.tm_mday, 23, 59, 59, 0, 0, 0))
    return start, end

def get_last_days_by_timestamp(day):
    now = time.localtime()
    t1 = time.mktime(
        (now.tm_year, now.tm_mon, now.tm_mday - day + 1, 0, 0, 0, 0, 0, 0))
    t2 = time.localtime(t1)
    start, _ = get_timestamp_interval(t2)
    _, end = get_timestamp_interval(now)
    return start, end

def get_last_days(day):
    now = time.localtime()
    t1 = time.mktime(
        (now.tm_year, now.tm_mon, now.tm_mday - day + 1, 0, 0, 0, 0, 0, 0))
    t2 = time.localtime(t1)
    start, _ = get_time_interval(t2)
    _, end = get_time_interval(now)
    return start, end

def get_query_timestamp(query_date):
    """获取查询日期的时间戳 """
    try:
        start_date = None
        end_date = None
        if query_date == "today":
            start_date, end_date = get_timestamp_interval(
                time.localtime())
        elif query_date == "yesterday":
            # day - 1
            now = time.localtime()
            yes_i = time.mktime((
                                now.tm_year, now.tm_mon, now.tm_mday - 1, 0,
                                0, 0, 0, 0, 0))
            yes = time.localtime(yes_i)
            start_date, end_date = get_timestamp_interval(yes)
        elif query_date.startswith("l"):
            days = int(query_date[1:])
            start_date, end_date = get_last_days_by_timestamp(days)
        else:
            if query_date.find("-") < 0:
                if query_date.isdigit():
                    s_time = time.strptime(query_date, "%Y%m%d")
                    start_date, end_date = get_timestamp_interval(
                        s_time)
            else:
                s, e = query_date.split("-")
                if s[-6:] == "000000" and e[-6:] == "000000":
                    s = s[:-6]
                    e = e[:-6]
                    start_time = time.strptime(s.strip(), "%Y%m%d")
                    end_time = time.strptime(e.strip(), "%Y%m%d")
                    start_date, _ = get_timestamp_interval(start_time)
                    _, end_date = get_timestamp_interval(end_time)
                else:
                    start_time = time.strptime(s.strip(), "%Y%m%d%H%M%S")
                    end_time = time.strptime(e.strip(), "%Y%m%d%H%M%S")
                    start_date = time.mktime(start_time)
                    end_date = time.mktime(end_time)

    except Exception as e:
        print("query timestamp exception:", str(e))
    return start_date, end_date

def get_query_date(query_date, begin=True):
    """获取查询日期
    
    查询日期的表示形式是以区间的格式表示，这里也考虑到了数据库里面实际存储的方式。
    在数据库里面是以小时为单位统计日志数据，所以这里的区间也是也小时来表示。
    比如表示今天，假设今天是2021/3/30，查询日期的格式是2021033000-2021033023。
    """
    try:
        start_date = None
        end_date = None
        if query_date == "today":
            start_date, end_date = get_time_interval(time.localtime())
        elif query_date == "yesterday":
            # day - 1
            now = time.localtime()
            yes_i = time.mktime((
                                now.tm_year, now.tm_mon, now.tm_mday - 1, 0,
                                0, 0, 0, 0, 0))
            yes = time.localtime(yes_i)
            start_date, end_date = get_time_interval(yes)
        elif query_date.startswith("l"):
            days = int(query_date[1:])
            start_date, end_date = get_last_days(days)
        else:
            if query_date.find("-") < 0:
                if query_date.isdigit():
                    s_time = time.strptime(query_date, "%Y%m%d")
                    start_date, end_date = get_time_interval(s_time)
            else:
                s, e = query_date.split("-")
                start_time = time.strptime(s.strip(), "%Y%m%d")
                start_date, _ = get_time_interval(start_time)
                end_time = time.strptime(e.strip(), "%Y%m%d")
                _, end_date = get_time_interval(end_time)

    except Exception as e:
        print("query date exception:", str(e))
    return start_date, end_date

def get_compare_date(query_start_date, compare_date):
    """获取对比日期"""
    try:
        start_date = time.strptime(str(query_start_date), "%Y%m%d%H")
        end_date = None
        if compare_date == "yesterday":
            yes_i = time.mktime((start_date.tm_year, start_date.tm_mon,
                                 start_date.tm_mday - 1, 0, 0, 0, 0, 0, 0))
            yes = time.localtime(yes_i)
            start_date, end_date = get_time_interval(yes)
        elif compare_date == "lw":
            week_i = time.mktime((start_date.tm_year, start_date.tm_mon,
                                  start_date.tm_mday - 7, 0, 0, 0, 0, 0, 0))
            week = time.localtime(week_i)
            start_date, end_date = get_time_interval(week)
        else:
            if compare_date.find("-") < 0:
                if compare_date.isdigit():
                    s_time = time.strptime(compare_date, "%Y%m%d")
                    start_date, end_date = get_time_interval(s_time)
            else:
                # print("区间时间：", compare_date)
                s, e = compare_date.split("-")
                start_time = time.strptime(s.strip(), "%Y%m%d")
                start_date, _ = get_time_interval(start_time)
                end_time = time.strptime(e.strip(), "%Y%m%d")
                _, end_date = get_time_interval(end_time)

        return start_date, end_date
    except Exception as e:
        print("compare date exception:", str(e))
    return None, None


#############sqlite####################


def export_sqlite_sql(db, tables="all", output_file=None):
    
    import sqlite3
    if os.path.exists(db):
        db = sqlite3.connect(db)
    else:
        return False

    cur = db.cursor()
    tables_str = ""
    if type(tables) == str:
        if tables == "all":
            pass
        elif tables.find(",") >= 0:
            tables_str = ["'"+t+"'" for t in tables.split(",") if t.strip()]
        else:
            tables_str = "'{}'".format(tables)
    else:
        tables_str = ["'"+t+"'" for t in tables]
    if tables == "all":
        results = cur.execute("select sql from sqlite_master").fetchall()
    else:
        select_sql = "select sql from sqlite_master where name in ({})".format(tables_str)
        results = cur.execute(select_sql).fetchall()
    sql_text = ""
    for res in results:
        if res[0]:
            if sql_text and sql_text != "None":
                sql_text += "\n"
            sql_text += res[0] +";"

    if output_file and sql_text:
        with open(output_file, "w", encoding="utf-8") as fp:
            fp.write(sql_text)
    return sql_text

def init_db_from(ori_db, new_db, tables="all"):
    try:
        sql_text = export_sqlite_sql(ori_db, tables=tables)
        if sql_text:
            import sqlite3
            conn = sqlite3.connect(new_db)
            cur = conn.cursor()
            cur.executescript(sql_text)
            conn.commit()
            cur.close()
            conn.close()
        if os.path.exists(new_db):
            return True
    except Exception as e:
        print("初始化异常：{}".format(e))
    return False

def get_file_json(filename, defaultv={}):
    try:
        if not os.path.exists(filename): return defaultv;
        return json.loads(public.readFile(filename))
    except:
        os.remove(filename)
        return defaultv

def get_site_settings(site):
    """获取站点配置"""

    config_path = "/www/server/total/config.json"
    config = get_file_json(config_path)

    res_config = {}
    if site not in config.keys():
        res_config = config["global"]
        res_config["push_report"] = False
    else:
        res_config = config[site]

    for k, v in config["global"].items():
        if k not in res_config.keys():
            if k == "push_report":
                res_config[k] = False
            else:
                res_config[k] = v
    return res_config

def get_site_name(siteName):
    db_file = '/www/server/total/logs/' + siteName + '/logs.db'
    if os.path.isfile(db_file): return siteName

    pid = public.M('sites').where('name=?', (siteName,)).getField('id');
    if not pid: 
        return siteName

    domains = public.M('domain').where('pid=?', (pid,)).field('name').select()
    for domain in domains:
        db_file = '/www/server/total/logs/' + domain["name"] + '/logs.db'
        if os.path.isfile(db_file): 
            siteName = domain['name']
            break
    return siteName.replace('_', '.')

def split_query_date(query_date):
    query_start, query_end = get_query_timestamp(query_date)
    today = time.strftime("%Y%m%d", time.localtime())
    _e = time.localtime(query_end)
    end = time.strftime("%Y%m%d", _e)
    query_array = []
    if today == end:
        query_array.append("today")

        _e = time.localtime(time.mktime((_e.tm_year, _e.tm_mon, _e.tm_mday-1, 0,0,0,0,0,0)))
        end_time = time.strftime("%Y%m%d", _e)
        _start, _end = get_query_timestamp(end_time)
        # print(query_start, _start)
        if query_start < _start:
            s = time.strftime("%Y%m%d000000", time.localtime(query_start))
            e = time.strftime("%Y%m%d000000", _e)
            query_str = "{}-{}".format(s, e)
            query_array.append(query_str)
    else:
        query_array.append(query_date)
    return query_array

def get_history_data_dir():
    default_history_data_dir = os.path.join(__backend_path, "logs")
    settings = get_site_settings("global")
    if "history_data_dir" in settings.keys():
        config_data_dir = settings["history_data_dir"]
    else:
        config_data_dir = default_history_data_dir
    history_data_dir = default_history_data_dir if not config_data_dir else config_data_dir
    return history_data_dir

def get_data_dir():
    default_data_dir = os.path.join(__backend_path, "logs")
    settings = get_site_settings("global")
    if "data_dir" in settings.keys():
        config_data_dir = settings["data_dir"]
    else:
        config_data_dir = default_data_dir
    data_dir = default_data_dir if not config_data_dir else config_data_dir
    return data_dir

def get_log_db_path(site, db_name="logs.db", history=False):
    if not history:
        data_dir = get_data_dir()
        db_path = os.path.join(data_dir, site, db_name)
    else:
        data_dir = get_history_data_dir()
        db_name = "history_logs.db"
        db_path = os.path.join(data_dir, site, db_name)
    return db_path