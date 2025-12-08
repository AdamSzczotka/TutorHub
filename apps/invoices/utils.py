from decimal import ROUND_HALF_UP, Decimal

# VAT rates for Poland
VAT_STANDARD = Decimal('0.23')  # 23%
VAT_REDUCED = Decimal('0.08')  # 8%
VAT_ZERO = Decimal('0.00')  # 0%


def round_currency(value) -> Decimal:
    """Round to 2 decimal places for currency."""
    return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def calculate_vat_from_net(net_amount, vat_rate=VAT_STANDARD) -> dict:
    """Calculate VAT from net amount.

    Args:
        net_amount: Net amount (before VAT).
        vat_rate: VAT rate as Decimal.

    Returns:
        Dict with net_amount, vat_amount, gross_amount, vat_rate.
    """
    net = Decimal(str(net_amount))
    vat = net * vat_rate
    gross = net + vat

    return {
        'net_amount': round_currency(net),
        'vat_amount': round_currency(vat),
        'gross_amount': round_currency(gross),
        'vat_rate': vat_rate,
    }


def calculate_vat_from_gross(gross_amount, vat_rate=VAT_STANDARD) -> dict:
    """Calculate VAT from gross amount.

    Args:
        gross_amount: Gross amount (with VAT).
        vat_rate: VAT rate as Decimal.

    Returns:
        Dict with net_amount, vat_amount, gross_amount, vat_rate.
    """
    gross = Decimal(str(gross_amount))
    net = gross / (1 + vat_rate)
    vat = gross - net

    return {
        'net_amount': round_currency(net),
        'vat_amount': round_currency(vat),
        'gross_amount': round_currency(gross),
        'vat_rate': vat_rate,
    }


def format_currency(amount) -> str:
    """Format amount as Polish currency.

    Args:
        amount: Amount to format.

    Returns:
        Formatted string like "1 234,56 zł".
    """
    amount = Decimal(str(amount))
    formatted = f"{amount:,.2f}".replace(',', ' ').replace('.', ',')
    return f"{formatted} zł"


def amount_to_words(amount) -> str:
    """Convert amount to Polish words.

    Args:
        amount: Amount to convert.

    Returns:
        Amount in Polish words with grosze as fraction.
    """
    units = [
        '',
        'jeden',
        'dwa',
        'trzy',
        'cztery',
        'pięć',
        'sześć',
        'siedem',
        'osiem',
        'dziewięć',
    ]
    teens = [
        'dziesięć',
        'jedenaście',
        'dwanaście',
        'trzynaście',
        'czternaście',
        'piętnaście',
        'szesnaście',
        'siedemnaście',
        'osiemnaście',
        'dziewiętnaście',
    ]
    tens = [
        '',
        '',
        'dwadzieścia',
        'trzydzieści',
        'czterdzieści',
        'pięćdziesiąt',
        'sześćdziesiąt',
        'siedemdziesiąt',
        'osiemdziesiąt',
        'dziewięćdziesiąt',
    ]
    hundreds = [
        '',
        'sto',
        'dwieście',
        'trzysta',
        'czterysta',
        'pięćset',
        'sześćset',
        'siedemset',
        'osiemset',
        'dziewięćset',
    ]

    amount = Decimal(str(amount))
    zlote, grosze = str(amount.quantize(Decimal('0.01'))).split('.')
    zlote_num = int(zlote)

    if zlote_num == 0:
        return f"zero złotych {grosze}/100"

    def convert_hundreds(num: int) -> str:
        result = ''
        h = num // 100
        t = (num % 100) // 10
        u = num % 10

        if h > 0:
            result += hundreds[h] + ' '

        if t == 1:
            result += teens[u] + ' '
        else:
            if t > 0:
                result += tens[t] + ' '
            if u > 0:
                result += units[u] + ' '

        return result

    result = ''

    # Thousands
    if zlote_num >= 1000:
        thousands = zlote_num // 1000
        result += convert_hundreds(thousands)
        if thousands == 1:
            result += 'tysiąc '
        elif 2 <= thousands % 10 <= 4 and not (12 <= thousands % 100 <= 14):
            result += 'tysiące '
        else:
            result += 'tysięcy '

    # Hundreds
    remainder = zlote_num % 1000
    if remainder > 0:
        result += convert_hundreds(remainder)

    # Currency suffix
    if zlote_num == 1:
        result += 'złoty'
    elif 2 <= zlote_num % 10 <= 4 and not (12 <= zlote_num % 100 <= 14):
        result += 'złote'
    else:
        result += 'złotych'

    result += f' {grosze}/100'

    return result.strip()
