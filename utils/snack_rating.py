from typing import Tuple


def get_snack(rating: int) -> Tuple[str, str, str]:
    """
    Map rating (1–10) -> (emoji, name, description).
    """
    rating = max(1, min(10, int(rating)))

    if rating >= 9:
        return (
            "🍛",
            "Porotta + Beef Roast",
            "Nee oru full meals mone! Resume kandappo chaaya kuda free ayi povum!",
        )
    if rating >= 7:
        return (
            "🍌",
            "Pazham Pori + Chaya",
            "Nallathu thanne! Chumma korachu polish cheythal top tier aakum.",
        )
    if rating >= 5:
        return (
            "🍪",
            "Parippu Vada Only",
            "Okay aanu… but upgrade cheyyanam. Projects & skills nanni polish cheyyu.",
        )
    if rating >= 3:
        return (
            "🥤",
            "Empty Glass Chaya",
            "Base undu, but content kurav aanu. Structure, clarity, examples okke add cheyyu.",
        )

    return (
        "💸",
        "Bill Kudukkan Pattilla",
        "Mone… puthiya start edukanam. Basic template use cheyth brand new resume ezhuth bro.",
    )
