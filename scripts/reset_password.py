import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_DIR / "src"

sys.path.insert(0, str(SRC_DIR))

from api.security import hash_password
from database.database import SessionLocal
from models.user import User


EMAIL = "wanderson.mendes@iz1.com.br"
NEW_PASSWORD = "12345678"


with SessionLocal() as session:

    user = (
        session.query(User)
        .filter(User.email == EMAIL)
        .first()
    )

    if user is None:
        print("Usuário não encontrado.")
        raise SystemExit

    user.password_hash = hash_password(
        NEW_PASSWORD,
    )

    session.commit()

    print("Senha alterada com sucesso.")
    print(f"Usuário: {user.name}")
    print(f"E-mail: {user.email}")