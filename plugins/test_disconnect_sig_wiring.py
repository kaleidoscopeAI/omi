"""Regression: every setup.html render in home() must carry disconnect_sig.

Why AST instead of importing main.py: the Hygiene lane has no fastapi. The bug
was a context dict missing a key, which is visible statically.
"""
import ast
import pathlib
import unittest

HERE = pathlib.Path(__file__).parent
APPS = ["omi-hive-app", "omi-linear-app", "omi-shipbob-app", "omi-shopify-app"]


def _dict_keys(node):
    return {k.value for k in node.keys if isinstance(k, ast.Constant)}


def _home_template_contexts(tree):
    for fn in ast.walk(tree):
        if isinstance(fn, (ast.AsyncFunctionDef, ast.FunctionDef)) and fn.name == "home":
            for call in ast.walk(fn):
                if isinstance(call, ast.Call) and getattr(call.func, "attr", "") == "TemplateResponse":
                    dicts = [a for a in call.args if isinstance(a, ast.Dict)]
                    dicts += [k.value for k in call.keywords if isinstance(k.value, ast.Dict)]
                    for d in dicts:
                        yield call.lineno, _dict_keys(d)


class DisconnectSigWiring(unittest.TestCase):
    def test_every_home_render_passes_disconnect_sig(self):
        for app in APPS:
            with self.subTest(app=app):
                tree = ast.parse((HERE / app / "main.py").read_text())
                contexts = list(_home_template_contexts(tree))
                self.assertTrue(contexts, f"{app}: found no TemplateResponse in home()")
                for lineno, keys in contexts:
                    self.assertIn("disconnect_sig", keys,
                                  f"{app}/main.py:{lineno} home() render omits disconnect_sig")


if __name__ == "__main__":
    unittest.main()
