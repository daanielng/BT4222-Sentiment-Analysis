from googleapiclient.discovery import build
from tqdm import tqdm

api_key = ''
youtube = build('youtube', 'v3', developerKey=api_key)

'''
Stocks of interest:
1) Apple, 2) Microsoft, 3) Google, 4) Nvidia, 5) Meta, 6) ASML Holdings, 7) Broadcom, 8) Adobe, 9) Cisco, 10) Qualcomm
'''

##function to get video titles, IDs, timestamps based on query
def get_video_titles_from_query(query, start_date = '2021-01-01T00:00:00Z', end_date = '2021-12-31T23:59:00Z', max_search=1000):
    #make request
    request = youtube.service.search().list(
            part = 'snippet',
            q = query, #query term to search for
            publishedAfter = start_date,
            publishedBefore = end_date,
            # order = 'viewCount', #resources sorted from highest to lowest views
            order = 'relevance',
            type = 'video',
            maxResults = 200
        )

    #dictionary to store video titles
    titles = {}
    titles['video ID'] = []
    titles['video title'] = []
    titles['timestamp'] = []
    titles['query'] = []
    
    while request:
        try:
            #execute request
            response = request.execute()
            
            #unpack each search resource
            for search_resource in tqdm(response['items']):
                
                #get search resource id
                search_id = search_resource['id']
                
                if 'videoId' in search_id:
                    video_id = search_resource['id']['videoId']
                    video_title = search_resource['snippet']['title']
                    video_timestamp = search_resource['snippet']['publishedAt']

                    #store info in dictionary
                    titles['video ID'].append(video_id)
                    titles['video title'].append(video_title)
                    titles['timestamp'].append(video_timestamp)
                    titles['query'].append(query)
            
            if len(titles)==max_search:
                return titles
            else:
                #retrieves next page of results
                try:
                    request = youtube.service.search().list(
                        part = 'snippet',
                        q = query, #query term to search for
                        publishedAfter = start_date,
                        publishedBefore = end_date,
                        order = 'viewCount', #resources sorted from highest to lowest views
                        type = 'video',
                        maxResults = 100,
                        pageToken = response['nextPageToken']
                        )
                except:
                    return titles
        
        except Exception as e:
            print(f'{query}: scrapping ended abruptly because of', e.__class__.__name__)
            return titles


##function to get video titles, IDs, timestamps from a channel
def get_video_titles_from_channel(channel_id):
    #make request
    request = youtube.service.search().list(
            part = 'snippet',
            channelId = channel_id,
            maxResults = 100
            )
    
    #dictionary to store video titles
    titles = {}
    titles['video ID'] = []
    titles['video title'] = []
    titles['timestamp'] = []
    titles['channel ID'] = []
    
    #execute request
    response = request.execute()

    #unpack each search resource
    for search_resource in tqdm(response['items']):
        
        #get search resource id
        search_id = search_resource['id']
        
        if 'videoId' in search_id:
            video_id = search_resource['id']['videoId']
            video_title = search_resource['snippet']['title']
            video_timestamp = search_resource['snippet']['publishedAt']

            titles['video ID'].append(video_id)
            titles['video title'].append(video_title)
            titles['timestamp'].append(video_timestamp)
            titles['channel ID'].append(channel_id)

    return titles


##function to get video comments, timestamps
def get_video_comments(video_id):
    #make request
    request = youtube.service.commentThreads().list(
        part = 'id, replies, snippet',
        videoId = video_id,
        maxResults = 1000
        )

    #dictionary to store comments
    comments = {}
    comments['timestamp'] = []
    comments['comment'] = []
    comments['video ID'] = []
    
    #nested function to get replies of comments
    def get_comment_replies(comment_id):
        #make request
        request = youtube.service.comments().list(
            part = 'id, snippet',
            parentId = comment_id,
            maxResults = 100
            )
        
        #dictionary to store comments resources
        replies = []
        
        while request:
            try:
                #execute request
                response = request.execute()
                
                #store comments resource
                replies.extend(response['items'])

                #retrieves next page of results
                request = youtube.service.comments().list_next(request, response)
            except:
                return replies
        return replies
    
    
    while request:
        try:
            #execute request
            response = request.execute()
            
            #unpack each comment resource
            for comment_resource in tqdm(response['items']):

                #get comment
                comments_resource = comment_resource['snippet']['topLevelComment']
                comment_text = comments_resource['snippet']['textOriginal']
                comment_timestamp = comments_resource['snippet']['publishedAt']
                
                #store comment in dictionary
                comments['timestamp'].append(comment_timestamp)
                comments['comment'].append(comment_text)
                comments['video ID'].append(video_id)

                #get all replies in response to top-level comment (within commentThreads resource)
                replies = comment_resource.get('replies')
                reply_count = comment_resource['snippet']['totalReplyCount'] #get total number of replies in response to top-level comment
                if replies is not None and reply_count != len(replies['comments']):
                    
                    #list of comments resources of replies to top-level comment
                    replies['comments'] = get_comment_replies(comment_resource['id'])
                    replies_comments_resource_list = replies['comments']
                    
                    for resource in replies_comments_resource_list:
                        reply_timestamp = resource['snippet']['publishedAt']
                        reply_text = resource['snippet']['textOriginal']
                        
                        #store reply in dictionary
                        comments['timestamp'].append(reply_timestamp)
                        comments['comment'].append(reply_text)
                        comments['video ID'].append(video_id)
                        
            #retrieves next page of results
            request = youtube.service.commentThreads().list_next(request, response)
        except Exception as e:
            print(f'{video_id}: scrapping ended abruptly because of', e.__class__.__name__)
            return comments
    return comments

