scheduleQuery = """
query($page: Int = 0, $amount: Int = 50, $watched: [Int!]!, $nextDay: Int!) {
  Page(page: $page, perPage: $amount) {
    pageInfo {
      currentPage
      hasNextPage
    }
    airingSchedules(notYetAired: true, mediaId_in: $watched, sort: TIME, airingAt_lesser: $nextDay) {
      media {
        id
        siteUrl
        format
        duration
        episodes
        title {
          romaji
        }
        coverImage {
          large
          color
        }
        externalLinks {
          site
          url
        }
        studios(isMain: true) {
          edges {
            isMain
            node {
              name
            }
          }
        }
      }
      episode
      airingAt
      timeUntilAiring
      id
    }
  }
}
"""

searchAni = """
query($name:String,$aniformat:MediaFormat,$page:Int,$amount:Int=5){
    Page(perPage:$amount,page:$page){
        pageInfo{hasNextPage, currentPage, lastPage}
        media(search:$name,type:ANIME,format:$aniformat){
            title {
                romaji, 
                english
            },
            id,
            format,
            episodes, 
            duration,
            status, 
            genres, 
            averageScore, 
            siteUrl,
            studios{nodes{name}}, 
            coverImage {large},
            bannerImage
        }
    } 
}
"""

generalQ = """
query($mediaId: Int){
    Media(id:$mediaId, type:ANIME){
        id,
        format,
        title {
            romaji, 
            english
        }, 
        episodes, 
        duration,
        status, 
        startDate {
            year, 
            month, 
            day
        }, 
        endDate {
            year, 
            month, 
            day
        }, 
        genres, 
        coverImage {
            large
        }, 
        bannerImage,
        description, 
        averageScore, 
        studios{nodes{name}}, 
        seasonYear, 
        externalLinks {
            site, 
            url
        } 
    } 
}
"""

listQ = """
query($page: Int = 0, $amount: Int = 50, $mediaId: [Int!]!) {
  Page(page: $page, perPage: $amount) {
    pageInfo {
      currentPage
      hasNextPage
    }
    media(id_in: $mediaId, type:ANIME){
        id,
        title {
            romaji,
            english
        },
        siteUrl,
        nextAiringEpisode {
            episode,
            airingAt,
            timeUntilAiring
        }
    }
  }
}
"""