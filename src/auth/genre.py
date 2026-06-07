from src.extensions import db

class Genre(db.Model):
    __tablename__ = 'genres'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image_file = db.Column(db.String(255), nullable=False)
    card_color = db.Column(db.String(50))

    def to_dict(self):
        """Chuyển đối tượng sang dictionary để dễ dàng jsonify."""
        return {
            'id': self.id,
            'name': self.name,
            'image_file': self.image_file,
            'card_color': self.card_color
        }