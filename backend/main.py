from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

APP_VERSION = "v2"

class TeamCreate(BaseModel):
    name: str
    stadium: str
    city: str

teams = [
    {"id": 1, "name": "Arsenal", "stadium": "Emirates Stadium", "city": "London"},
    {"id": 2, "name": "Aston Villa", "stadium": "Villa Park", "city": "Birmingham"},
    {"id": 3, "name": "Bournemouth", "stadium": "Vitality Stadium", "city": "Bournemouth"},
    {"id": 4, "name": "Brentford", "stadium": "Gtech Community Stadium", "city": "London"},
    {"id": 5, "name": "Brighton", "stadium": "Amex Stadium", "city": "Brighton"},
    {"id": 6, "name": "Burnley", "stadium": "Turf Moor", "city": "Burnley"},
    {"id": 7, "name": "Chelsea", "stadium": "Stamford Bridge", "city": "London"},
    {"id": 8, "name": "Crystal Palace", "stadium": "Selhurst Park", "city": "London"},
    {"id": 9, "name": "Everton", "stadium": "Hill Dickinson Stadium", "city": "Liverpool"},
    {"id": 10, "name": "Fulham", "stadium": "Craven Cottage", "city": "London"},
    {"id": 11, "name": "Liverpool", "stadium": "Anfield", "city": "Liverpool"},
    {"id": 12, "name": "Manchester City", "stadium": "Etihad Stadium", "city": "Manchester"},
    {"id": 13, "name": "Manchester United", "stadium": "Old Trafford", "city": "Manchester"},
    {"id": 14, "name": "Newcastle United", "stadium": "St James' Park", "city": "Newcastle"},
    {"id": 15, "name": "Nottingham Forest", "stadium": "City Ground", "city": "Nottingham"},
    {"id": 16, "name": "Sunderland", "stadium": "Stadium of Light", "city": "Sunderland"},
    {"id": 17, "name": "Tottenham Hotspur", "stadium": "Tottenham Hotspur Stadium", "city": "London"},
    {"id": 18, "name": "West Ham United", "stadium": "London Stadium", "city": "London"},
    {"id": 19, "name": "Wolverhampton Wanderers", "stadium": "Molineux Stadium", "city": "Wolverhampton"},
    {"id": 20, "name": "Leeds United", "stadium": "Elland Road", "city": "Leeds"},
]


@app.get("/teams")
def get_teams():
    return teams

@app.get("/teams/{team_id}")
def get_team(team_id: int):
    for team in teams:
        if team["id"] == team_id:
            return team

    raise HTTPException(status_code=404, detail="Team not found")


@app.get("/version")
def get_version():
    return {"version": APP_VERSION}

@app.post("/teams")
def create_team(team: TeamCreate):
    new_team = {
        "id": len(teams) + 1,
        "name": team.name,
        "stadium": team.stadium,
        "city": team.city,
    }

    teams.append(new_team)

    return new_team