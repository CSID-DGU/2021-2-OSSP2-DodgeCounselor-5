from requests.models import HTTPError
from riotwatcher import LolWatcher
from riotwatcher._apis.league_of_legends.SummonerApiV4 import SummonerApiV4
from riotwatcher._apis.league_of_legends.MatchApiV5 import MatchApiV5
import app.functions.functions as fun
import time as t

DeathKingScore = 20
NoItemScore = 10
BadSpellScore = 10
DamageDiffWeight = 2
GoldDiffWeight = 3
visionScoreWeight = 3

def calculateScorePerUser(userName, target) :
    print("함수 시작")
    start_time = t.time()
    summonerDTO = fun.getSummonerInfo(userName)
    matchList = fun.getMatchBySummonerDTO(summonerDTO, 20)
    matchInfos = fun.getMatchInfoByMatchID(matchList)
    print("데이터 받아오기 끝 :", round(t.time() - start_time, 3))

    resultSet = {
        "userName" : userName,
        "deathKingCount" : 0,
        "badItemCount" : 0,
        "badSpellCount" : 0,
        "weakDamageCount" : 0,
        "lackGoldCount" : 0,
        "visionLowCount" : 0,
        "trollScore" : [],
        "totalScore" : 0
    }

    for i in range(len(matchInfos)) :
        #처음에 0점짜리 추가
        resultSet['trollScore'].append(0)

        userLoc = fun.getUserLoc(matchInfos[i], summonerDTO['name'])

        #DeathKing 구하는 부분
        if (fun.DeathKing(matchInfos[i], userLoc)) :
            resultSet['trollScore'][i] += DeathKingScore
            resultSet['deathKingCount'] += 1

        #noItem 구하는 부분
        if (fun.buySameItems(matchInfos[i], userLoc)) :
            resultSet['trollScore'][i] += NoItemScore
            resultSet['badItemCount'] += 1

        #badSpell 구하는 부분
        if (not(fun.UseCorrectSpell(matchInfos[i], userLoc))) :
            resultSet['trollScore'][i] += BadSpellScore
            resultSet['badSpellCount'] += 1
        
        #딜량 차이 구하는 부분
        damageDiff = fun.damageDiffByPosition(matchInfos[i], userLoc)
        if (damageDiff != 0) :
            resultSet['trollScore'][i] += (damageDiff * DamageDiffWeight)
            resultSet['weakDamageCount'] += 1

        #골드 차이 구하는 부분
        goldDiff = fun.goldDiffByPostion(matchInfos[i], userLoc)
        if (goldDiff != 0) :
            resultSet['trollScore'][i] += (goldDiff * GoldDiffWeight)
            resultSet['lackGoldCount'] += 1

        #시야점수 차이 구하는 부분
        visionDiff = fun.visionScoreDiffByPosition(matchInfos[i], userLoc)
        if (visionDiff != 0) :
            resultSet['trollScore'][i] += (visionDiff * visionScoreWeight)
            resultSet['visionLowCount'] += 1

        resultSet['trollScore'][i] = round(resultSet['trollScore'][i])

        resultSet['totalScore'] += resultSet['trollScore'][i]

    print("분석 끝 :", round(t.time() - start_time, 3))

    target.append(resultSet)