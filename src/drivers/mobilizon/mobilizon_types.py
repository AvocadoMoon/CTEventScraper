from pydantic import BaseModel
from enum import Enum

def _generate_args(localVariables: dict) -> dict:
    args = {}
    for name, value in localVariables.items():
        if (value is not None and name != "self" and name != "__class__"):
            args[name] = value
    return args

class EventParameters:
    class Status(Enum):
        confirmed = "CONFIRMED"
        canceled = "CANCELED"
        tentative = "TENTATIVE"

    class Category(Enum):
        category = "CATEGORY"

    class Visibility(Enum):
        public = "PUBLIC"
    
    class JoinOptions(Enum):
        free = "FREE"
        invite = "INVITE"
        restricted = "RESTRICTED"
    
    class Categories(Enum):
        arts = "ARTS".upper()
        book_clubs = "BOOK_CLUBS".upper()
        business = "BUSINESS"
        causes = "CAUSES"
        comedy = "COMEDY"
        crafts = "CRAFTS"
        food_drink = "FOOD_DRINK"
        health = "HEALTH"
        music = "MUSIC"
        community = "COMMUNITY"
        family_education = "FAMILY_EDUCATION"
        fashion_beauty = "FASHION_BEAUTY"
        film_media = "FILM_MEDIA"
        games = "GAMES"
        language_culture = "LANGUAGE_CULTURE"
        learning = "LEARNING"
        lgbtq = "LGBTQ"
        movements_politics = "MOVEMENTS_POLITICS"
        networking = "NETWORKING"
        party = "PARTY"
        performing_visual_arts = "PERFORMING_VISUAL_ARTS"
        pets = "PETS"
        photography = "PHOTOGRAPHY"
        outdoors_adventure = "OUTDOORS_ADVENTURE"
        spirituality_religion_beliefs = "SPIRITUALITY_RELIGION_BELIEFS"
        science_tech = "SCIENCE_TECH"
        sports = "SPORTS"
        theatre = "THEATRE"
        default = "MEETING"

    class Address(BaseModel):
        """Address object that Mobilizon can utilize

        Args:
            geom: State
            locality: Town
            postalCode: ZipCode
            street: Street
            country: Country
        """
        geom: str = None # State
        locality: str  # Town
        postalCode: str # ZipCode
        street: str # Street
        country: str # 
        
        def __init__(self, locality:str, postalCode:str, street:str, country:str, geom:str = None):
            args = _generate_args(locals())
            super().__init__(**args)
    
    class MediaInput(BaseModel):
        media_id: int = None
    
    
        


class EventType(BaseModel):
    """_summary_

    Args:
        OrganizerActorId: Actor ID
        AttributedToId: Group ID
    """
    
    organizerActorId: int = 0 # Actor ID
    attributedToId: int = 0 # Group ID
    title: str = ""
    description: str = None
    beginsOn: str = "2020-10-29T00:00:00+01:00"
    endsOn: str = None
    status: EventParameters.Status = EventParameters.Status.confirmed
    visibility: EventParameters.Visibility = EventParameters.Visibility.public
    joinOptions: EventParameters.JoinOptions = EventParameters.JoinOptions.free
    draft: str = None
    tags: list[str] = []
    picture: EventParameters.MediaInput = None # https://github.com/framasoft/mobilizon/blob/main/lib/graphql/schema/media.ex
    onlineAddress: str = None
    phoneAddress: str = None
    category: EventParameters.Categories = None
    physicalAddress: EventParameters.Address = None
    # options: dict = {}
    contacts: str = None
    
    def __init__(self, attributedToId:int, title: str, description: str, 
                          beginsOn:str, onlineAddress:str = None, endsOn:str = None,
                          physicalAddress: EventParameters.Address = None,
                          category: EventParameters.Categories = None, tags:[] = None):
        args = _generate_args(locals())
        super().__init__(**args)


class Actor(BaseModel):
    id: int
    name: str
    preferredUsername: str
    type: str
    url: str
    
    def __init__(self, id: int, name: str, preferredUsername: str, type: str, url:str):
        args = _generate_args(locals())
        super().__init__(**args)
    
# print(isinstance(EventParameters.MediaInput(), (BaseModel)))


