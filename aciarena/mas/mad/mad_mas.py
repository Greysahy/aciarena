import re
import ast
import json
from aciarena.mas import BaseMAS
from aciarena.mas.mad.agents import *
from aciarena.utils.factory import register_mas
from aciarena.mas.mad.prompt import *

@register_mas("mad")
class MAD(BaseMAS):
    def __init__(self, llm_config, logger, malicious_agents=['negative'], max_turn=2):
        self.judge_prompt_last2 = ""
        self.round = 0
        super().__init__(llm_config, malicious_agents, logger, max_turn)
    
    def init_agents(self):
        return {
            "affirmative": AffirmativeAgent(llm_config=self.llm_config),
            "negative": NegativeAgent(llm_config=self.llm_config),
            "moderator": ModeratorAgent(llm_config=self.llm_config),
            "judge": JudgeAgent(llm_config=self.llm_config)
        }
    
    def init_prompt(self, debate_topic):
        player_meta_prompt = PLAYER_META_PROMPT.replace("##debate_topic##", debate_topic)
        moderator_prompt = MODERATOR_META_PROMPT.replace("##debate_topic##", debate_topic)
        affirmative_prompt = AFFIRMATIVE_PROMPT.replace("##debate_topic##", debate_topic)
        judge_prompt_last2 = JUDGE_PROMPT_LAST2.replace("##debate_topic##", debate_topic)

        self.get_agent("affirmative").update_profile(player_meta_prompt)
        self.get_agent("negative").update_profile(player_meta_prompt)
        self.get_agent("moderator").update_profile(moderator_prompt)
        self.get_agent("judge").update_profile(moderator_prompt)

        return affirmative_prompt, judge_prompt_last2

    def _log_step(self, sender, receiver, message):
        self.logger.log_message(sender=sender, receiver=receiver, message=message)

    def round_dct(self, num: int):
        dct = {
            1: 'first', 2: 'second', 3: 'third', 4: 'fourth', 5: 'fifth',
            6: 'sixth', 7: 'seventh', 8: 'eighth', 9: 'ninth', 10: 'tenth'
        }
        return dct.get(num, f"{num}th")
    
    def _safe_parse(self, text):
        """去掉多余标记并安全解析成 Python 对象"""
        cleaned = re.sub(r"```json|```", "", text).strip()
        try:
            result = ast.literal_eval(cleaned)
            if isinstance(result, dict):
                return result
            else:
                return {"debate_answer": cleaned}
        except Exception:
            return {}  # 解析失败时返回空字典

    def _dialog_loop(self, neg_response, round):
        self._log_step(sender="negative", receiver="affirmative", message=neg_response)
        affirmative_prompt = DEBATE_PROMPT.replace('##oppo_ans##', neg_response)
        aff_response = self.get_agent("affirmative").run_step(affirmative_prompt)
                
        self._log_step(sender="affirmative", receiver="negative", message=neg_response)
        negative_prompt = DEBATE_PROMPT.replace('##oppo_ans##', aff_response)
        neg_response = self.get_agent("negative").run_step(negative_prompt)

        self._log_step(sender="affirmative & negative", receiver="moderator", message="aff:" + aff_response + "\n" + "neg:" + neg_response)
        moderator_prompt = MODERATOR_PROMPT.replace('##aff_ans##', aff_response).replace('##neg_ans##', neg_response).replace('##round##', self.round_dct(round+2))
        
        # 修复1：保存 step() 的返回值
        mod_response_raw = self.get_agent("moderator").run_step(moderator_prompt)
        # 修复2：安全解析
        mod_response = self._safe_parse(mod_response_raw)

        return neg_response, mod_response, aff_response

    def bootstrap(self, query): 
        debate_topic = query
        self._log_step(sender="user", receiver="affirmative", message=query)
        affirmative_prompt, self.judge_prompt_last2 = self.init_prompt(debate_topic)
        aff_response = self.get_agent("affirmative").run_step(affirmative_prompt)

        self._log_step(sender="affirmative", receiver="negative", message=aff_response)
        negative_prompt = NEGATIVE_PROMPT.replace('##aff_ans##', aff_response)
        neg_response = self.get_agent("negative").run_step(negative_prompt)

        self._log_step(sender="affirmative & negative", receiver="moderator", message="aff:" + aff_response + "\n" + "neg" + neg_response)
        moderator_prompt = MODERATOR_PROMPT.replace('##aff_ans##', aff_response).replace('##neg_ans##', neg_response).replace('##round##', 'first')
        mod_response_raw = self.get_agent("moderator").run_step(moderator_prompt)
        mod_response = self._safe_parse(mod_response_raw)

        if mod_response.get("debate_answer"):
            response = mod_response["debate_answer"]
            self._log_step(sender="moderator", receiver="user", message=response)
            return {"response": response}, True

        return {"neg_response": neg_response, "mod_response": mod_response, "aff_response": aff_response}, False

    def step(self, args):
        neg_response = args["neg_response"]
        neg_response, mod_response, aff_response = self._dialog_loop(neg_response, self.round)
        self.round += 1
        if mod_response.get("debate_answer"):
            response = mod_response["debate_answer"]
            self._log_step(sender="moderator", receiver="user", message=response)
            return {"response": response}, True
        
        return {"neg_response": neg_response, "mod_response": mod_response, "aff_response": aff_response}, False

    def conclude(self, args):
        if args.get("response"):
            return args
        else:
            mod_response = args["mod_response"]
            aff_response = args["aff_response"]
            neg_response = args["neg_response"]

            if mod_response.get("debate_answer"):
                response = mod_response["debate_answer"]
                self._log_step(sender="moderator", receiver="user", message=response)
                args["response"] = response

            else:
                self._log_step(sender="affirmative & negative", receiver="judge", message="aff:" + aff_response + "\n" + "neg" + neg_response)
                judge_prompt1 = JUDGE_PROMPT_LAST1.replace('##aff_ans##', aff_response).replace('##neg_ans##', neg_response)
                judge_response_raw = self.get_agent("judge").run_step(judge_prompt1)

                judge_response = self._safe_parse(judge_response_raw)

                if judge_response.get("debate_answer"):
                    response = judge_response["debate_answer"]
                    self._log_step(sender="judge", receiver="user", message=response)
                    args["response"] = response
                
                else:
                    self._log_step(sender="judge", receiver="user", message=judge_response)
                    args["response"] = str(judge_response)
        
        return args
