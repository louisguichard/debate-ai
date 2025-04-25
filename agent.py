class Agent:
    def __init__(self, name, role, persona=""):
        self.name = name
        self.role = role
        self.persona = persona

    def __str__(self):
        return f"{self.name} ({self.role})"

    def to_dict(self):
        return {
            "name": self.name,
            "role": self.role,
            "persona": self.persona,
        }
