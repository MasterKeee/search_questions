import requests
import plugins
from plugins import *
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger


@plugins.register(name="search_questions",
                  desc="描述",
                  version="1.0",
                  author="masterke",
                  desire_priority=100)
class search_questions(Plugin):
    content = None
    config_data = None

    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info(f"[{__class__.__name__}] inited")

    def get_help_text(self, **kwargs):
        help_text = f"获取早报信息"
        return help_text

    def on_handle_context(self, e_context: EventContext):
        # 只处理文本消息
        if e_context['context'].type != ContextType.TEXT:
            return
        self.content = e_context["context"].content.strip()

        if self.content.startswith("搜题"):
            logger.info(f"[{__class__.__name__}] 收到消息: {self.content}")
            # 读取配置文件
            config_path = os.path.join(os.path.dirname(__file__),
                                       "config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as file:
                    self.config_data = json.load(file)
            else:
                logger.error(f"请先配置{config_path}文件")
                return

            reply = Reply()
            result = self.search_questions()
            if result != None:
                reply.type = ReplyType.TEXT
                reply.content = result
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS
            else:
                reply.type = ReplyType.ERROR
                reply.content = "获取失败,等待修复⌛️"
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS

    def search_questions(self):
        if self.content.startswith("搜题 "):
            self.content.replace("搜题 ", "")
        elif self.content.startswith("搜题"):
            self.content.replace("搜题", "")
        try:
            #主接口
            url = f"https://tk.enncy.cn/query"
            params = f"token={self.config_data['token']}&title={self.content}&more=true"
            headers = {'Content-Type': "application/x-www-form-urlencoded"}
            response = requests.get(url=url,
                                    params=params,
                                    headers=headers,
                                    timeout=10)
            if response.status_code == 200:
                json_data = response.json()
                if json_data.get('code') == 1 and json_data['data']['results']:
                    data = json_data['data']['results']
                    text = ""
                    for item in data:
                        text += f"【问题】{item['question'].strip()}\n【答案】{item['answer'].strip()}"
                        if len(data) == 1:
                            continue
                        else:
                            text += "\n----------------\n"
                    text = text.strip()
                    logger.info(f"主接口获取成功:{json_data}")
                    return text
                elif json_data.get('code') == 0:
                    return "❌未找到答案"
                else:
                    logger.error(f"主接口未找到答案或返回参数异常:{json_data}")
                    raise ValueError('not found data')
            else:
                logger.error(f"主接口请求失败:{response.status_code}")
                raise requests.ConnectionError
        except Exception as e:
            logger.error(f"主接口抛出异常:{e}")
            # try:
            #     #备用接口
            #     url = ""
            #     payload = ""
            #     headers = {'Content-Type': "application/x-www-form-urlencoded"}
            #     response = requests.post(url=url,
            #                              data=payload,
            #                              headers=headers,
            #                              timeout=4)
            #     if response.status_code == 200:
            #         json_data = response.json()
            #         if json_data.get('code') == "200" and json_data[""]:
            #             text = f""
            #             logger.info(f"备用接口获取成功:{json_data}")
            #             return text
            #         else:
            #             logger.error(f"备用接口返回参数异常:{json_data}")
            #     else:
            #         logger.error(f"备用接口请求失败:{response.status_code}")
            # except Exception as e:
            #     logger.error(f"备用接口抛出异常:{e}")

        logger.error(f"所有接口都挂了,无法获取")
        return None
