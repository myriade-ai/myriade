from back.models import Note, Project


class NoteService:
    def __init__(self, session, id: str):
        self.session = session
        self.note = self.session.query(Note).filter_by(id=id).first()

    def read(self):
        return self.note.content

    def update(self, title: str, content: str):
        self.note.title = title
        self.note.content = content
        self.session.flush()


class Notes:
    def __init__(self, session, chat, project: Project):
        self.session = session
        self.chat = chat
        self.project = project

    def create_note(self, title: str, content: str):
        note = Note(projectId=self.project.id, title=title, content=content)
        self.session.add(note)
        self.session.flush()
        return "Created note with id " + str(note.id)

    def list_notes(self):
        notes = self.session.query(Note).filter_by(projectId=self.project.id).all()
        return [{"id": note.id, "title": note.title} for note in notes]

    def delete_note(self, id: str):
        """Delete a note from the project"""
        note = (
            self.session.query(Note).filter_by(id=id, projectId=self.project.id).first()
        )
        if note:
            self.session.delete(note)
            self.session.flush()

    def open_note(self, id: int):
        note = NoteService(session=self.session, id=id)
        if note:
            return self.chat.add_tool(note)
        else:
            raise ValueError(f"Note with id {id} not found")

    def close_note(self, id: int):
        return self.chat.remove_tool(id)
