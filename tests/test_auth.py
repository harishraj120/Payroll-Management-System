import unittest
from payroll.auth import hash_password, verify_password


class PasswordTests(unittest.TestCase):
    def test_hash_verifies_correct_password(self):
        encoded = hash_password("ExamplePass123!")
        self.assertTrue(verify_password("ExamplePass123!", encoded))

    def test_wrong_password_is_rejected(self):
        encoded = hash_password("ExamplePass123!")
        self.assertFalse(verify_password("WrongPass123!", encoded))

    def test_salts_make_hashes_different(self):
        first = hash_password("ExamplePass123!")
        second = hash_password("ExamplePass123!")
        self.assertNotEqual(first, second)
        self.assertTrue(verify_password("ExamplePass123!", first))

    def test_short_password_is_rejected(self):
        with self.assertRaises(ValueError):
            hash_password("short")


if __name__ == "__main__":
    unittest.main()
