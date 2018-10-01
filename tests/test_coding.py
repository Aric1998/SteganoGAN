#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `deepsteganography.coding` package."""

import unittest
from random import random

from deepsteganography.coding import (
    bits_to_text, bytearray_to_text, text_to_bits, text_to_bytearray)

CORPUS = [
    "Hello world!",
    "This is a random string.",
    "\00 is going to mess things up"
]


class TestCoding(unittest.TestCase):
    """Tests for `deepsteganography.coding` package."""

    def test_text_bytearray(self):
        """Test conversions between text and bytearrays."""
        for text in CORPUS:
            data = text_to_bytearray(text)
            self.assertEqual(text, bytearray_to_text(data))

    def test_text_bits(self):
        """Test conversions between text and bit lists."""
        for text in CORPUS:
            data = text_to_bits(text)
            self.assertEqual(text, bits_to_text(data))

    def test_text_bits_corrupted(self):
        """Test conversions between text and corrupted bit."""
        for text in CORPUS:
            data = text_to_bits(text)
            for i in range(len(data)):
                # corrupt 10% of bits
                if random() < 0.1:
                    data[i] = 0
            self.assertEqual(text, bits_to_text(data))
