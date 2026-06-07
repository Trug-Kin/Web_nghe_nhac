from src.extensions import db

class Artist(db.Model):
    __tablename__ = 'artists'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    image_file = db.Column(db.String(255), nullable=False)
    
    def to_dict(self):
        """Chuyển đối tượng sang dictionary để dễ dàng jsonify."""
        return {
            'id': self.id,
            'name': self.name,
            'image_file': self.image_file
        }