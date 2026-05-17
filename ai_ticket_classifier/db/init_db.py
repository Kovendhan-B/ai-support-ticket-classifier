from ai_ticket_classifier.db.session import engine
from ai_ticket_classifier.db.models import Base

def init_db():
    print("Creating database tables..")
    Base.metadata.create_all(bind=engine)
    print("Done.")

if __name__ == "__main__":
    init_db()