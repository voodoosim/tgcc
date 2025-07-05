import re
from typing import Optional, Tuple


def normalize_phone_number(phone: str) -> Optional[str]:
    """
    전화번호를 정규화합니다.
    - 모든 특수문자, 공백, 하이픈, 괄호 등 제거
    - + 기호는 맨 앞에만 유지
    - 숫자만 남김

    예시:
    +1 (234) 567-8900 -> +12345678900
    +82 10 1234 5678 -> +821012345678
    +888 0749 3574 -> +88807493574
    888-0749-3574 -> 88807493574
    (880) 749 3574 -> 8807493574
    """
    if not phone:
        return None

    # 전체 문자열에서 + 기호가 맨 앞에 있는지 확인
    has_leading_plus = phone.strip().startswith("+")

    # 숫자만 추출 (모든 특수문자, 공백 제거)
    digits = re.sub(r"[^\d]", "", phone)

    if not digits:
        return None

    # + 기호 복원 (맨 앞에만)
    if has_leading_plus:
        return "+" + digits

    return digits


def extract_country_code(phone: str) -> Tuple[Optional[str], Optional[str]]:
    """
    전화번호에서 국가 코드를 추출합니다.

    Returns:
        (country_code, remaining_number)
    """
    normalized = normalize_phone_number(phone)
    if not normalized:
        return None, None

    # + 제거
    digits = normalized.lstrip("+")

    # 일반적인 국가 코드들
    country_codes = {
        "1": "USA/Canada",
        "7": "Russia/Kazakhstan",
        "20": "Egypt",
        "27": "South Africa",
        "30": "Greece",
        "31": "Netherlands",
        "32": "Belgium",
        "33": "France",
        "34": "Spain",
        "36": "Hungary",
        "39": "Italy",
        "40": "Romania",
        "41": "Switzerland",
        "43": "Austria",
        "44": "UK",
        "45": "Denmark",
        "46": "Sweden",
        "47": "Norway",
        "48": "Poland",
        "49": "Germany",
        "51": "Peru",
        "52": "Mexico",
        "53": "Cuba",
        "54": "Argentina",
        "55": "Brazil",
        "56": "Chile",
        "57": "Colombia",
        "58": "Venezuela",
        "60": "Malaysia",
        "61": "Australia",
        "62": "Indonesia",
        "63": "Philippines",
        "64": "New Zealand",
        "65": "Singapore",
        "66": "Thailand",
        "81": "Japan",
        "82": "South Korea",
        "84": "Vietnam",
        "86": "China",
        "90": "Turkey",
        "91": "India",
        "92": "Pakistan",
        "93": "Afghanistan",
        "94": "Sri Lanka",
        "95": "Myanmar",
        "98": "Iran",
        "212": "Morocco",
        "213": "Algeria",
        "216": "Tunisia",
        "218": "Libya",
        "220": "Gambia",
        "221": "Senegal",
        "222": "Mauritania",
        "223": "Mali",
        "224": "Guinea",
        "225": "Ivory Coast",
        "226": "Burkina Faso",
        "227": "Niger",
        "228": "Togo",
        "229": "Benin",
        "230": "Mauritius",
        "231": "Liberia",
        "232": "Sierra Leone",
        "233": "Ghana",
        "234": "Nigeria",
        "235": "Chad",
        "236": "Central African Republic",
        "237": "Cameroon",
        "238": "Cape Verde",
        "239": "São Tomé and Príncipe",
        "240": "Equatorial Guinea",
        "241": "Gabon",
        "242": "Republic of the Congo",
        "243": "Democratic Republic of the Congo",
        "244": "Angola",
        "245": "Guinea-Bissau",
        "246": "British Indian Ocean Territory",
        "247": "Ascension Island",
        "248": "Seychelles",
        "249": "Sudan",
        "250": "Rwanda",
        "251": "Ethiopia",
        "252": "Somalia",
        "253": "Djibouti",
        "254": "Kenya",
        "255": "Tanzania",
        "256": "Uganda",
        "257": "Burundi",
        "258": "Mozambique",
        "260": "Zambia",
        "261": "Madagascar",
        "262": "Réunion",
        "263": "Zimbabwe",
        "264": "Namibia",
        "265": "Malawi",
        "266": "Lesotho",
        "267": "Botswana",
        "268": "Eswatini",
        "269": "Comoros",
        "290": "Saint Helena",
        "291": "Eritrea",
        "297": "Aruba",
        "298": "Faroe Islands",
        "299": "Greenland",
        "350": "Gibraltar",
        "351": "Portugal",
        "352": "Luxembourg",
        "353": "Ireland",
        "354": "Iceland",
        "355": "Albania",
        "356": "Malta",
        "357": "Cyprus",
        "358": "Finland",
        "359": "Bulgaria",
        "370": "Lithuania",
        "371": "Latvia",
        "372": "Estonia",
        "373": "Moldova",
        "374": "Armenia",
        "375": "Belarus",
        "376": "Andorra",
        "377": "Monaco",
        "378": "San Marino",
        "380": "Ukraine",
        "381": "Serbia",
        "382": "Montenegro",
        "383": "Kosovo",
        "385": "Croatia",
        "386": "Slovenia",
        "387": "Bosnia and Herzegovina",
        "389": "North Macedonia",
        "420": "Czech Republic",
        "421": "Slovakia",
        "423": "Liechtenstein",
        "500": "Falkland Islands",
        "501": "Belize",
        "502": "Guatemala",
        "503": "El Salvador",
        "504": "Honduras",
        "505": "Nicaragua",
        "506": "Costa Rica",
        "507": "Panama",
        "508": "Saint Pierre and Miquelon",
        "509": "Haiti",
        "590": "Guadeloupe",
        "591": "Bolivia",
        "592": "Guyana",
        "593": "Ecuador",
        "594": "French Guiana",
        "595": "Paraguay",
        "596": "Martinique",
        "597": "Suriname",
        "598": "Uruguay",
        "599": "Curaçao",
        "670": "East Timor",
        "672": "Australian External Territories",
        "673": "Brunei",
        "674": "Nauru",
        "675": "Papua New Guinea",
        "676": "Tonga",
        "677": "Solomon Islands",
        "678": "Vanuatu",
        "679": "Fiji",
        "680": "Palau",
        "681": "Wallis and Futuna",
        "682": "Cook Islands",
        "683": "Niue",
        "685": "Samoa",
        "686": "Kiribati",
        "687": "New Caledonia",
        "688": "Tuvalu",
        "689": "French Polynesia",
        "690": "Tokelau",
        "691": "Micronesia",
        "692": "Marshall Islands",
        "850": "North Korea",
        "852": "Hong Kong",
        "853": "Macau",
        "855": "Cambodia",
        "856": "Laos",
        "880": "Bangladesh",
        "886": "Taiwan",
        "960": "Maldives",
        "961": "Lebanon",
        "962": "Jordan",
        "963": "Syria",
        "964": "Iraq",
        "965": "Kuwait",
        "966": "Saudi Arabia",
        "967": "Yemen",
        "968": "Oman",
        "970": "Palestine",
        "971": "United Arab Emirates",
        "972": "Israel",
        "973": "Bahrain",
        "974": "Qatar",
        "975": "Bhutan",
        "976": "Mongolia",
        "977": "Nepal",
        "992": "Tajikistan",
        "993": "Turkmenistan",
        "994": "Azerbaijan",
        "995": "Georgia",
        "996": "Kyrgyzstan",
        "998": "Uzbekistan",
    }

    # 국가 코드 매칭 (긴 것부터 시도)
    for length in [3, 2, 1]:
        if len(digits) >= length:
            possible_code = digits[:length]
            if possible_code in country_codes:
                return possible_code, digits[length:]

    return None, digits


def validate_phone_number(phone: str) -> bool:
    """
    전화번호 유효성 검사
    - 최소 4자리 이상 (단축 번호 허용)
    - 숫자로만 구성 (+ 제외)
    - 최대 15자리 (국제 표준)
    """
    normalized = normalize_phone_number(phone)
    if not normalized:
        return False

    # + 제거하고 검사
    digits = normalized.lstrip("+")

    # 최소 4자리, 최대 15자리
    return digits.isdigit() and 4 <= len(digits) <= 15


def format_phone_display(phone: str) -> str:
    """
    전화번호를 보기 좋게 포맷팅 (표시용)
    """
    normalized = normalize_phone_number(phone)
    if not normalized:
        return phone

    # 국가 코드 추출
    country_code, number = extract_country_code(normalized)

    # number가 None인 경우 처리
    if not number:
        number = ""

    if country_code and normalized.startswith("+"):
        # 국가별 포맷팅 (일부 예시)
        if country_code == "82" and number:  # 한국
            if len(number) == 10 and number.startswith("10"):
                return f"+{country_code} {number[:2]} {number[2:6]} {number[6:]}"
            elif len(number) == 9 and number.startswith("2"):
                return f"+{country_code} {number[:1]} {number[1:5]} {number[5:]}"
        elif country_code == "1" and number:  # 미국/캐나다
            if len(number) == 10:
                return f"+{country_code} ({number[:3]}) {number[3:6]}-{number[6:]}"
        elif country_code == "880" and number:  # 방글라데시
            if len(number) >= 8:
                return f"+{country_code} {number[:4]} {number[4:]}"

    # 기본 포맷 (4자리씩 구분)
    if normalized.startswith("+"):
        result = normalized[:2]  # +와 첫 숫자
        remaining = normalized[2:]
    else:
        result = ""
        remaining = normalized

    # 4자리씩 공백으로 구분
    for i in range(0, len(remaining), 4):
        if result:
            result += " "
        result += remaining[i : i + 4]

    return result


def guess_country_from_number(phone: str) -> Optional[str]:
    """
    전화번호에서 국가 추측
    """
    country_code, _ = extract_country_code(phone)

    if country_code:
        country_names = {
            "1": "미국/캐나다",
            "7": "러시아/카자흐스탄",
            "82": "한국",
            "86": "중국",
            "81": "일본",
            "91": "인도",
            "880": "방글라데시",
            "44": "영국",
            "49": "독일",
            "33": "프랑스",
            # ... 더 많은 국가 추가 가능
        }
        return country_names.get(country_code, f"국가코드 +{country_code}")

    return None
