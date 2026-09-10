import pytest

from app.utils.slipgenerator import (
    ALPHABET,
    SlipGenerator,
    SlipGeneratorError,
    generate_slips,
    next_code,
)


def test_alphabet_shape():
    assert len(ALPHABET) == 33
    # No ambiguous characters
    assert set(ALPHABET) & {"0", "I", "O"} == set()


def test_next_code_basic_increment():
    assert next_code("A1") == "A2"
    assert next_code("BC8GMS6X") == "BC8GMS6Y"
    assert next_code("A9") == "AA"


def test_next_code_carry_within_code():
    assert next_code("AZ") == "B1"
    assert next_code("BZ") == "C1"
    assert next_code("1Z") == "21"


def test_next_code_wrap_grows_code():
    assert next_code("Z") == "11"
    assert next_code("ZZ") == "111"
    assert next_code("ZZZ") == "1111"


def test_next_code_roundtrip_through_alphabet():
    # Every non-last symbol advances to the next symbol
    for i, char in enumerate(ALPHABET[:-1]):
        assert next_code(f"A{char}") == f"A{ALPHABET[i + 1]}"


def test_next_code_invalid_char():
    with pytest.raises(SlipGeneratorError):
        next_code("B0GUS")


def test_next_code_empty():
    assert next_code("") == ALPHABET[0]


def test_generate_slips_count_and_order():
    codes = generate_slips("AZ", 5)
    assert codes == ["AZ", "B1", "B2", "B3", "B4"]


def test_generate_slips_zero_or_negative():
    assert generate_slips("A1", 0) == []
    assert generate_slips("A1", -3) == []


def test_slip_generator_wrapper():
    gen = SlipGenerator()
    assert gen.generateSlip("AZ", 3) == ["AZ", "B1", "B2"]
