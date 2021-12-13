from typing import Mapping
from requests.models import HTTPError
from riotwatcher import LolWatcher
from riotwatcher._apis.league_of_legends.SummonerApiV4 import SummonerApiV4
from riotwatcher._apis.league_of_legends.MatchApiV5 import MatchApiV5
key = 'RGAPI-e540e4bc-8f24-4821-b8de-0e5cc8539d01' #제한시간 없음
key2 = 'RGAPI-ba006b9f-bbef-4093-b2d0-084e727de2f1' #제한시간 1일
watcher = [
    LolWatcher(key),
    LolWatcher(key2)
]

def nameSlice(input) :   #멀티서치 기능을 위해 사용되는 함수
    player = input.split(". ")
    for i in range(len(player)) :
        for j in range(len(player[i])) :
            if (player[i][j] == '님') and (player[i][j+1] == '이') and (player[i][j+2] == " ") :    
                player[i] = player[i][0:j]
                break
    return player

def getSummonerInfo(playerName) :   #PlayerName을 이용하여 PlayerName에 따른 SummonerDTO를 반환해주는 함수
    #infoList에 플레이어들의 정보(SummonerDTO)가 리스트로 담김
    return watcher[0].summoner.by_name("KR", playerName) 

def getMatchBySummonerDTO(infoList, gameCount) :     #SummonDTO에서 얻을 수 있는 puuid를 이용하여 최근 n개의 게임에 대한
    return watcher[0].match.matchlist_by_puuid("asia", infoList['puuid'], None, gameCount, None, "ranked")   #Puuid를 이용하여 각 유저의 랭크게임 gameCount개에 대한 MatchID 가져오기

def getUserLoc(matchInfo, playerName) :
    for i in range (10) :
        if playerName == matchInfo['info']['participants'][i]['summonerName'] :
            return i

def getMatchInfoByMatchID(matchList) :
    matchInfo = []
    for i in range(len(matchList)) :
        matchInfo.append(watcher[i%2].match.by_id('asia', matchList[i]))
    return matchInfo

def DeathKing(matchInfo, userLoc):
    #데스수가 게임시간-5 보다 크거나 같으면 대가리 박은걸로 간주
    gameDuration = matchInfo['info']['gameDuration']
    gameDuration = gameDuration / 60
    print("게임 시간 :", gameDuration)
    death_count = matchInfo['info']['participants'][userLoc]['deaths']
    
    if death_count >= gameDuration - 5:
        return True
    else:
        return False

def buySameItems(singleMatchInfo, playerNum) : #어떤 게임에서 한 플레이어가 같은 아이템을 3개 이상 구매했는가?
    count = 0
    noItem = True
    item = []
    item.append(singleMatchInfo['info']['participants'][playerNum]['item0'])
    item.append(singleMatchInfo['info']['participants'][playerNum]['item1'])
    item.append(singleMatchInfo['info']['participants'][playerNum]['item2'])
    item.append(singleMatchInfo['info']['participants'][playerNum]['item3'])
    item.append(singleMatchInfo['info']['participants'][playerNum]['item4'])
    item.append(singleMatchInfo['info']['participants'][playerNum]['item5'])

    for i in range(6) :
        if (item[i] != 0) :
            noItem = False

    for i in range(6) :
        for j in range(i + 1, 6) :
            if (item[i] == item[j] and item[i] != 0) :
                count += 1        

    if (count >= 3 or noItem) :
        return True
    else :
        return False


def UseCorrectSpell(singleMatchInfo, playerNum) : #한 게임에서 플레이어 포지션에 따른 스펠의 적절성 체크
    if singleMatchInfo['info']['participants'][playerNum]['teamPosition'] == "JUNGLE" : #포지션이 정글인 경우
        if singleMatchInfo['info']['participants'][playerNum]['summoner1Id'] == 11 or singleMatchInfo['info']['participants'][playerNum]['summoner2Id'] == 11 :
            return True     #강타 있으면 승패 상관없이 True
        else :
            return False    #정글러가 강타 없으면 승패 상관없이 False

    else :  #정글러가 아닌 경우
        if singleMatchInfo['info']['participants'][playerNum]['summoner1Id'] == 11 or singleMatchInfo['info']['participants'][playerNum]['summoner2Id'] == 11 :
            if (singleMatchInfo['info']['participants'][playerNum]['win']) :    
                return True     #정글러가 아닌데 강타 들었어도, 이겼으면 True
            else :
                return False    #정글러가 아닌데 강타 들고 졌으면? False

        else :  #강타 안들었으면 True
            return True

def damageDiffByPosition(matchInfo, userLoc):
    pos = matchInfo['info']['participants'][userLoc]['teamPosition']
    otherPlayerLoc = 0
    if pos=='UTILITY': #서폿은 나가있어
        return 0

    # 자신과 같은 position의 딜량찾기
    if userLoc < 5:
        for j in range(5,10):
            if matchInfo['info']['participants'][j]['teamPosition'] == pos:
                otherPlayerLoc = j
                break
    else:
         for j in range(0,5):
            if matchInfo['info']['participants'][j]['teamPosition'] == pos:
                otherPlayerLoc = j
                break

    # 같은 포지션의 딜량을 나누어서 몇배인지 확인
    dmgDiff = matchInfo['info']['participants'][otherPlayerLoc]['totalDamageDealt'] / matchInfo['info']['participants'][userLoc]['totalDamageDealt']      

    # 3배 이상 차이나면 그냥 3을 반환, 그렇게 차이가 크지 않다면 그 값을 반환
    if dmgDiff >= 3 :
        return 3
    elif dmgDiff >= 2 :
        return dmgDiff
    else:
        return 0

def goldDiffByPostion(matchInfo, userLoc) :
    pos = matchInfo['info']['participants'][userLoc]['teamPosition']
    otherPlayerLoc = 0

    if pos=='UTILITY': #서폿은 나가있어
        return 0

    # 자신과 같은 position의 위치 찾기
    if userLoc < 5:
        for j in range(5,10):
            if matchInfo['info']['participants'][j]['teamPosition'] == pos:
                otherPlayerLoc = j
                break
    else:
         for j in range(0,5):
            if matchInfo['info']['participants'][j]['teamPosition'] == pos:
                otherPlayerLoc = j
                break

    # 같은 포지션의 두명   
    goldDiff = matchInfo['info']['participants'][otherPlayerLoc]['goldEarned'] / matchInfo['info']['participants'][userLoc]['goldEarned']

    # 3배 넘게 차이나면 그냥 3을 반환, 그렇게 차이가 크지 않다면 값 자체를 반환
    if goldDiff >= 3 :
        return 3
    elif goldDiff >= 1.2 :
        return goldDiff
    else:
        return 0

def visionScoreDiffByPosition(matchInfo, userLoc) :
    pos = matchInfo['info']['participants'][userLoc]['teamPosition']
    otherPlayerLoc = 0

    if pos=='UTILITY': #서폿은 나가있어
        return 0

    # 자신과 같은 position의 위치 찾기
    if userLoc < 5:
        for j in range(5,10):
            if matchInfo['info']['participants'][j]['teamPosition'] == pos:
                otherPlayerLoc = j
                break
    else:
         for j in range(0,5):
            if matchInfo['info']['participants'][j]['teamPosition'] == pos:
                otherPlayerLoc = j
                break
    try :
        vScoreDiff = matchInfo['info']['participants'][otherPlayerLoc]['visionScore'] / matchInfo['info']['participants'][userLoc]['visionScore']
    except :
        return 0
    
    #3배 넘게 차이나면 그냥 3을 반환, 그렇게 차이가 크지 않다면 값 자체를 반환
    if vScoreDiff >= 5 :
        return 5
    elif vScoreDiff >= 1.2 :
        return vScoreDiff
    else:
        return 0


""" def visionWardsBought(i): 
    if visionWards[i] == 0: #제어와드 구매횟수가 0인 경우
        return 5
    else:
        return 0 """

""" def noSupItem(i):
    number = ['0','1','2','3','4','5']
    sup_item = [3850,3851,3853,3854,3855,3857,3858,3859,3860,3862,3863,3864] # 현 버전 서폿템 리스트
    itemlist=[]
    count = 0
    if position[i] == 'UTILITY': #서폿인경우
        for num in number:
            itemlist.append(matchData['info']['participants'][i]['item'+num])
    else: #그외
        return 0
    print(itemlist)
    for item in itemlist: #아이템0~아이템5 
        for sitem in sup_item: #서폿템 
            if item == sitem: #서폿템이 있으면
                return 0
            else:
                continue

    print("서폿템 없다")
    return 5 #서폿템이 없는 경우 """