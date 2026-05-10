import json
import random
import os
import math

class QuestionGenerator:
    def __init__(self, json_file='data/questions.json'):
        self.json_file = json_file
        self.questions = []
        self._load_questions()

    def _load_questions(self):
        if os.path.exists(self.json_file):
            with open(self.json_file, 'r', encoding='utf-8') as f:
                self.questions = json.load(f)

    def _solve_executor(self, start, end):
        commands = []
        while start > end:
            if start % 2 == 0 and start // 2 >= end:
                commands.append("1")
                start //= 2
            else:
                commands.append("2")
                start -= 1
        return ''.join(commands)

    def _evaluate(self, expr, params):
        try:
            namespace = {
                "bin": bin, "oct": oct, "hex": hex,
                "int": int, "len": len, "sum": sum,
                "all": all, "eval": eval, "math": math,
                "solve_executor": self._solve_executor
            }
            namespace.update(params)

            if isinstance(expr, str) and expr.strip().startswith("lambda"):
                return str(eval(expr, namespace)(*params.values()))
            else:
                result = eval(expr, namespace)
                if isinstance(result, float):
                    if result.is_integer():
                        return str(int(result))
                    return str(result)
                return str(result)
        except Exception as e:
            print(f"Ошибка: {expr} | {e}")
            return "ERROR"

    def generate_question(self):
        if not self.questions:
            return {"text": "Ошибка: список заданий пуст", "answer": "ERROR"}
        template = random.choice(self.questions)
        ttype = template.get("type")

        if ttype == "variants":
            variant = random.choice(template["variants"])
            text = template["text"].format(**variant)
            return {"text": text, "answer": str(variant["answer"])}

        if ttype == "binary":
            length = random.randint(4, 8)
            chars = ['А', 'Б', 'В', 'Г']
            codes = {'А': '00', 'Б': '01', 'В': '10', 'Г': '11'}
            word = ''.join(random.choice(chars) for _ in range(length))
            code = ''.join(codes[ch] for ch in word)
            text = template["text"].format(code=code)
            return {"text": text, "answer": word}

        if ttype == "executor":
            start = random.choice(template["params"]["start"])
            end = random.choice(template["params"]["end"])
            text = template["text"].format(start=start, end=end)
            answer = self._solve_executor(start, end)
            return {"text": text, "answer": answer}

        params = {}
        for key, val in template.get("params", {}).items():
            if isinstance(val, list) and len(val) == 2 and all(isinstance(v, int) for v in val):
                params[key] = random.randint(val[0], val[1])
            elif isinstance(val, list):
                params[key] = random.choice(val)
            else:
                params[key] = val

        text = template["text"].format(**params)

        if "formula" in template:
            answer = self._evaluate(template["formula"], params)
        elif "answer" in template:
            answer = template["answer"]
        else:
            answer = "ERROR"

        return {"text": text, "answer": str(answer)}