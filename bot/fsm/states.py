from aiogram.fsm.state import State, StatesGroup


class AuthState(StatesGroup):
    waiting_phone = State()


class AdminCreateUser(StatesGroup):
    waiting_phone = State()
    waiting_name = State()
    waiting_role = State()


class AdminCreateProject(StatesGroup):
    waiting_title = State()
    waiting_description = State()
    waiting_status = State()
    waiting_owner = State()
    waiting_start_date = State()


class ProjectTitleUpdate(StatesGroup):
    waiting_title = State()


class ProjectDescriptionUpdate(StatesGroup):
    waiting_description = State()


class ProjectOwnerUpdate(StatesGroup):
    waiting_owner = State()


class ProjectStatusUpdate(StatesGroup):
    waiting_status = State()
