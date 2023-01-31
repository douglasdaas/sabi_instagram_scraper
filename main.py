from instaloader import Instaloader, Profile, ProfileNotExistsException, QueryReturnedBadRequestException
from csv import reader, writer, DictWriter
import time


def append_dict_to_csv(data: dict):
    field_names = [key for key in data]

    with open('user_data.csv', 'a') as f_object:
        dictwriter_object = DictWriter(f_object, fieldnames=field_names)
        dictwriter_object.writerow(data)
        f_object.close()


def clean_username(bad_username):
    cleaned_user = bad_username
    if cleaned_user.startswith('@'):
        cleaned_user = cleaned_user[1:]
    if cleaned_user.endswith('/'):
        cleaned_user = cleaned_user[:-1]
    if cleaned_user.startswith('https://www.instagram.com/'):
        cleaned_user = cleaned_user.split('/')[3]
    return cleaned_user


def scrape(username):
    profile = Profile.from_username(L.context, username)
    # last_month_user_info = get_last_month_info(username)

    user_data = {
        'user_id': profile.userid,
        'account_type': profile._metadata('category_name'),
        'account_is_business': profile.is_business_account,
        'followers_count': profile.get_followers().count,
        'post_count': profile.get_posts().count,
        'account_name': profile.full_name,
        'bio': profile.biography.replace('\n', ' '),
        'bio_links': profile.external_url,
        'email': profile._metadata('business_email'),
        'total_comments': 0
    }

    stats = {
        'GraphImage': {
            'comments_count': 0,
            'likes_count': 0,
            'hashtags_set': set(),
            'sponsors_set': set(),
            'tagged_users_set': set(),
            'count': 0,
            'likes_average': 0,
            'comments_average': 0,
        },
        'GraphVideo': {
            'comments_count': 0,
            'likes_count': 0,
            'hashtags_set': set(),
            'sponsors_set': set(),
            'tagged_users_set': set(),
            'videos_total_views': 0,
            'count': 0,
            'likes_average': 0,
            'comments_average': 0,
        },
        'GraphSidecar': {
            'comments_count': 0,
            'likes_count': 0,
            'hashtags_set': set(),
            'sponsors_set': set(),
            'tagged_users_set': set(),
            'count': 0,
            'likes_average': 0,
            'comments_average': 0,
        }
    }
    posts = profile.get_posts()
    # count = 1
    print(f'Total posts: {posts.count}')
    for post in profile.get_posts():
        # print(f'post: {count} of {posts.count}')
        # count += 1
        post_type = post.typename
        stats[post_type]['comments_count'] += post.comments
        stats[post_type]['likes_count'] += post.likes
        stats[post_type]['hashtags_set'].update(post.caption_hashtags)
        stats[post_type]['sponsors_set'].update(post.sponsor_users)
        stats[post_type]['tagged_users_set'].update(post.tagged_users)
        stats[post_type]['count'] += 1

        if post.is_video:
            stats[post_type]['videos_total_views'] += post.video_view_count

    for media_type in ['GraphImage', 'GraphVideo', 'GraphSidecar']:
        media_type_count = stats[media_type]['count']
        likes_counts = stats[media_type]['likes_count']
        comments_counts = stats[media_type]['comments_count']

        if media_type_count != 0:
            stats[media_type]['likes_average'] = round(likes_counts / media_type_count, 2)
            stats[media_type]['comments_average'] = round(comments_counts / media_type_count, 2)
        else:
            stats[media_type]['likes_average'] = 0
            stats[media_type]['comments_average'] = 0

        user_data['total_comments'] += stats[media_type]['comments_count']

    # profile_grow = ((last_month_user_info['followers_count'] - user_data['followers_count']) * 100) / last_month_user_info['followers_count']
    # comments_grow = ((last_month_user_info['total_comments'] - user_data['total_comments']) * 100) / last_month_user_info['total_comments']
    user_data['stats'] = stats

    return user_data, posts.count


if __name__ == '__main__':
    # start_time = time.time()
    L = Instaloader()
    L.load_session_from_file('hellosabi.app')
    count_success_profile = 0
    count_fail_profiles = 0

    with open('instagram_users_1.csv') as csv_file:
        csv_reader = reader(csv_file, delimiter=',')
        for row in csv_reader:
            if row:
                cleaned_user = clean_username(row[0])
                print(f'Fetching: {cleaned_user}')
                profile_time = time.time()
                try:
                    user_data, post_count = scrape(cleaned_user)
                    # print(user_data)
                    append_dict_to_csv(user_data)
                    count_success_profile += 1
                    print(f'execution time on {cleaned_user} profile: {round((time.time() - profile_time), 2)} seconds')
                    print(f'{cleaned_user} has {post_count} media posts')

                except ProfileNotExistsException as err:
                    print(err)
                    with open('profile_not_found.csv', 'a') as f_object:
                        writer_object = writer(f_object)
                        string_error = str(err)
                        suggested_username_list_string = 'No suggestions'
                        if string_error.find('The most similar profiles are:') > 0:
                            suggested_username_list_string = string_error.split(':')[1][:-1].strip()
                        writer_object.writerow([cleaned_user, suggested_username_list_string])
                        count_fail_profiles += 1
                        f_object.close()
                    print(f'Profile: {cleaned_user} added with suggestions to profile_not_found.csv')

                except QueryReturnedBadRequestException as err:
                    raise Exception("Open Firefox, log into the instagram account and re-run 615_import_firefox_session.py")

        csv_file.close()
    print(f'execution time: {round((time.time() - profile_time), 2)} seconds')
    print(f'Profiles successfully fetch: {count_success_profile}')
    print(f'Profiles failed to fetch: {count_fail_profiles}')


    # username = 'victorsabii'
    # user_data = scrape(username)
