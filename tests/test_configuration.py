"""Offline-only regression tests; no provider credentials or connections."""
import ast
import importlib
import os
from pathlib import Path
import unittest
from unittest.mock import patch

config = importlib.import_module('runtime_config')
ROOT = Path(__file__).resolve().parents[1]


class ConfigurationTests(unittest.TestCase):
    def test_missing_value_fails_without_secret(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, 'UNIT_TEST_REQUIRED'):
                config.required_env('UNIT_TEST_REQUIRED')

    def test_blank_value_fails(self):
        with patch.dict(os.environ, {'UNIT_TEST_REQUIRED': '  '}, clear=True):
            with self.assertRaises(RuntimeError):
                config.required_env('UNIT_TEST_REQUIRED')

    def test_supplied_value_is_used(self):
        with patch.dict(os.environ, {'UNIT_TEST_REQUIRED': 'offline-fixture'}, clear=True):
            self.assertEqual(config.required_env('UNIT_TEST_REQUIRED'), 'offline-fixture')

    def test_sources_compile(self):
        for name in ['pythonService.py', 'runtime_config.py', 'gun.py']:
            compile((ROOT / name).read_bytes(), name, 'exec')


    def test_all_required_config_and_default_port(self):
        values = {'REDIS_PASSWORD': 'offline-redis', 'MINIAPP_APP_ID': 'offline-app',
                  'MINIAPP_SECRET': 'offline-app-secret'}
        with patch.dict(os.environ, values, clear=True):
            actual = config.load_config()
            self.assertEqual(actual['redis_port'], 6379)
            self.assertEqual(actual['redis_password'], values['REDIS_PASSWORD'])
            self.assertEqual(actual['miniapp_secret'], values['MINIAPP_SECRET'])
        for missing in values:
            with patch.dict(os.environ, {k: v for k, v in values.items() if k != missing}, clear=True):
                with self.assertRaisesRegex(RuntimeError, missing):
                    config.load_config()

    def test_no_tracked_private_key_in_tree(self):
        self.assertFalse(list(ROOT.glob('*.key')))
