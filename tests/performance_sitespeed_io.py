# -*- coding: utf-8 -*-
from pathlib import Path
import os
from models import Rating
import datetime
import config
from tests.utils import *
import gettext
_local = gettext.gettext

sitespeed_use_docker = config.sitespeed_use_docker


def get_result(sitespeed_use_docker, arg):

    result = ''
    if sitespeed_use_docker:
        dir = Path(os.path.dirname(
            os.path.realpath(__file__)) + os.path.sep).parent
        data_dir = dir.resolve()

        bashCommand = "docker run --rm -v {1}:/sitespeed.io sitespeedio/sitespeed.io:latest {0}".format(
            arg, data_dir)

        import subprocess
        process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
        result = str(output)
    else:
        import subprocess

        bashCommand = "node node_modules{1}sitespeed.io{1}bin{1}sitespeed.js {0}".format(
            arg, os.path.sep)

        process = subprocess.Popen(
            bashCommand.split(), stdout=subprocess.PIPE)

        output, error = process.communicate()
        result = str(output)

    return result


def run_test(_, langCode, url):
    """
    Checking an URL against Sitespeed.io (Docker version). 
    For installation, check out:
    - https://hub.docker.com/r/sitespeedio/sitespeed.io/
    - https://www.sitespeed.io
    """
    language = gettext.translation(
        'performance_sitespeed_io', localedir='locales', languages=[langCode])
    language.install()
    _local = language.gettext

    print(_local('TEXT_RUNNING_TEST'))

    print(_('TEXT_TEST_START').format(
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    rating = Rating(_)
    result_dict = {}

    # We have this first so it can take any penalty of servers sleeping
    no_external_result_dict = validate_on_mobile_no_external_domain(
        url)

    # We have this second so it can take any left penalty of servers sleeping
    nojs_result_dict = validate_on_mobile_no_javascript(url)

    # Are they still not ready they need to fix it...
    desktop_result_dict = validate_on_desktop(url)

    mobile_result_dict = validate_on_mobile(url)

    desktop_rating = rate_result_dict(desktop_result_dict, None,
                                      'desktop', _, _local)
    rating += desktop_rating
    result_dict.update(desktop_result_dict)

    mobile_rating = rate_result_dict(mobile_result_dict, None,
                                     'mobile', _, _local)
    rating += mobile_rating
    result_dict.update(mobile_result_dict)

    no_external_rating = rate_result_dict(no_external_result_dict, mobile_result_dict,
                                          'mobile no third parties', _, _local)

    nojs_rating = rate_result_dict(nojs_result_dict, mobile_result_dict,
                                   'mobile no js', _, _local)

    if mobile_rating.get_overall() < no_external_rating.get_overall():
        # points = 5.0 - (no_external_rating.get_overall() -
        #                 mobile_rating.get_overall())
        # tmp_rating = Rating(_)
        # tmp_rating.set_overall(
        #     points, '- [mobile] Advice: Rating mey improve from {0} to {1} by removing some/all external resources'.format(mobile_rating.get_overall(), no_external_rating.get_overall()) )
        # rating += tmp_rating
        rating.overall_review += '- [mobile] Advice: Rating may improve from {0} to {1} by removing some/all external resources'.format(
            mobile_rating.get_overall(), no_external_rating.get_overall())
    rating += no_external_rating
    result_dict.update(no_external_result_dict)

    if mobile_rating.get_overall() < nojs_rating.get_overall():
        # points = 5.0 - (nojs_rating.get_overall() -
        #                 mobile_rating.get_overall())
        # tmp_rating = Rating(_)
        # tmp_rating.set_overall(
        #     points, '- [mobile] Advice: Performance rating could be improved by removing some/all javascript files')
        # rating += tmp_rating
        rating.overall_review += '- [mobile] Advice: Rating may improve from {0} to {1} by removing some/all javascript resources'.format(
            mobile_rating.get_overall(), no_external_rating.get_overall())

    rating += nojs_rating
    result_dict.update(nojs_result_dict)

    print(_('TEXT_TEST_END').format(
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    return (rating, result_dict)


def validate_on_mobile_no_external_domain(url):
    o = urllib.parse.urlparse(url)
    hostname = o.hostname

    if hostname.startswith('www.'):
        tmp_url = url.replace(hostname, hostname[4:])
        o = urllib.parse.urlparse(tmp_url)
        hostname = o.hostname

    arg = '--shm-size=1g -b chrome --blockDomainsExcept *.{2} --mobile true --connectivity.profile 3gfast --visualMetrics true --plugins.remove screenshot --speedIndex true --xvfb --browsertime.videoParams.createFilmstrip false --browsertime.chrome.args ignore-certificate-errors -n {0} {1}'.format(
        config.sitespeed_iterations, url, hostname)
    if 'nt' in os.name:
        arg = '--shm-size=1g -b chrome --mobile true --connectivity.profile 3gfast --visualMetrics true --plugins.remove screenshot --speedIndex true --browsertime.videoParams.createFilmstrip false --browsertime.chrome.args ignore-certificate-errors -n {0} {1}'.format(
            config.sitespeed_iterations, url)

    result_dict = get_result_dict(get_result(
        sitespeed_use_docker, arg), 'mobile no third parties')

    return result_dict


def validate_on_mobile_no_javascript(url):
    arg = '--shm-size=1g -b chrome --block .js --mobile true --connectivity.profile 3gfast --visualMetrics true --plugins.remove screenshot --speedIndex true --xvfb --browsertime.videoParams.createFilmstrip false --browsertime.chrome.args ignore-certificate-errors --browsertime.chrome.args disable-javascript -n {0} {1}'.format(
        config.sitespeed_iterations, url)
    if 'nt' in os.name:
        arg = '--shm-size=1g -b chrome --block .js --mobile true --connectivity.profile 3gfast --visualMetrics true --plugins.remove screenshot --speedIndex true --browsertime.videoParams.createFilmstrip false --browsertime.chrome.args ignore-certificate-errors --browsertime.chrome.args disable-javascript -n {0} {1}'.format(
            config.sitespeed_iterations, url)

    result_dict = get_result_dict(get_result(
        sitespeed_use_docker, arg), 'mobile no js')

    return result_dict


def validate_on_desktop(url):
    arg = '--shm-size=1g -b chrome --connectivity.profile native --visualMetrics true --plugins.remove screenshot --speedIndex true --xvfb --browsertime.videoParams.createFilmstrip false --browsertime.chrome.args ignore-certificate-errors -n {0} {1}'.format(
        config.sitespeed_iterations, url)
    if 'nt' in os.name:
        arg = '--shm-size=1g -b chrome --connectivity.profile native --visualMetrics true --plugins.remove screenshot --speedIndex true --browsertime.videoParams.createFilmstrip false --browsertime.chrome.args ignore-certificate-errors -n {0} {1}'.format(
            config.sitespeed_iterations, url)

    result_dict = get_result_dict(get_result(
        sitespeed_use_docker, arg), 'desktop')

    return result_dict


def validate_on_mobile(url):
    arg = '--shm-size=1g -b chrome --mobile true --connectivity.profile 3gfast --visualMetrics true --plugins.remove screenshot --speedIndex true --xvfb --browsertime.videoParams.createFilmstrip false --browsertime.chrome.args ignore-certificate-errors -n {0} {1}'.format(
        config.sitespeed_iterations, url)
    if 'nt' in os.name:
        arg = '--shm-size=1g -b chrome --mobile true --connectivity.profile 3gfast --visualMetrics true --plugins.remove screenshot --speedIndex true --browsertime.videoParams.createFilmstrip false --browsertime.chrome.args ignore-certificate-errors -n {0} {1}'.format(
            config.sitespeed_iterations, url)

    result_dict = get_result_dict(get_result(
        sitespeed_use_docker, arg), 'mobile')

    return result_dict


def rate_result_dict(result_dict, reference_result_dict, mode, _, _local):
    limit = 500

    rating = Rating(_)
    performance_review = ''
    overview_review = ''

    if reference_result_dict != None:
        external_to_remove = list()
        for pair in reference_result_dict.items():
            key = pair[0]
            mobile_obj = pair[1]
            key_matching = False

            if key not in result_dict:
                continue

            noxternal_obj = result_dict[key]

            if 'median' not in mobile_obj:
                continue
            if 'median' not in noxternal_obj:
                continue

            value_diff = 0
            if mobile_obj['median'] > (limit + noxternal_obj['median']):
                value_diff = mobile_obj['median'] - noxternal_obj['median']
                # tmp_points = 5.0 - ((value_diff / limit) * 0.5)

                # tmp_rating = Rating(_)
                txt = ''
                if 'mobile no third parties' in mode:
                    txt = '- [mobile] Advice: {0} may improve by {1:.2f}ms by removing external resources\r\n'.format(
                        key, value_diff)
                elif 'mobile no js' in mode:
                    txt = '- [mobile] Advice: {0} may improve by {1:.2f}ms by removing javascript resources\r\n'.format(
                        key, value_diff)

                overview_review += txt
                # tmp_rating.set_overall(
                #     tmp_points, txt)
                # rating += tmp_rating
                key_matching = True

            if 'range' not in mobile_obj:
                continue
            if 'range' not in noxternal_obj:
                continue

            value_diff = 0
            if mobile_obj['range'] > (limit + noxternal_obj['range']):
                value_diff = mobile_obj['range'] - noxternal_obj['range']
                # tmp_points = 5.0 - ((value_diff / limit) * 0.5)
                # tmp_rating = Rating(_)
                txt = ''
                if 'mobile no third parties' in mode:
                    txt = '- [mobile] Advice: {0} could be ±{1:.2f}ms less "bumpy" by removing external resources\r\n'.format(
                        key, value_diff)
                elif 'mobile no js' in mode:
                    txt = '- [mobile] Advice: {0} could be ±{1:.2f}ms less "bumpy" by removing javascript resources\r\n'.format(
                        key, value_diff)

                overview_review += txt
                # tmp_rating.set_overall(
                #     tmp_points, txt)
                # rating += tmp_rating
                key_matching = True

            if not key_matching:
                external_to_remove.append(key)

        for key in external_to_remove:
            del result_dict[key]

    # points = float(result_dict['Points'])

    # review_overall = ''
    # if True or mode == 'desktop' or mode == 'mobile':
    #     if points >= 5.0:
    #         review_overall = _local('TEXT_REVIEW_VERY_GOOD')
    #     elif points >= 4.0:
    #         review_overall = _local('TEXT_REVIEW_IS_GOOD')
    #     elif points >= 3.0:
    #         review_overall = _local('TEXT_REVIEW_IS_OK')
    #     elif points > 1.0:
    #         review_overall = _local('TEXT_REVIEW_IS_BAD')
    #     elif points <= 1.0:
    #         review_overall = _local('TEXT_REVIEW_IS_VERY_BAD')

    if 'Points' in result_dict:
        del result_dict['Points']

    # summary_rating = Rating(_)
    # summary_rating.set_overall(points, review_overall.replace(
    #     '- ', '- [{0}] '.format(mode)))
    # summary_rating.set_performance(points, review)

    # review = summary_rating.performance_review
    for pair in result_dict.items():
        value = pair[1]
        if 'msg' not in value:
            continue
        if 'points' in value and value['points'] != -1:
            points = value['points']
            entry_rating = Rating(_)
            entry_rating.set_overall(points)
            entry_rating.set_performance(
                points, value['msg'])
            rating += entry_rating
        else:
            performance_review += '{0}\r\n'.format(value['msg'])

    # review += _local("TEXT_REVIEW_NUMBER_OF_REQUESTS").format(
    #     result_dict['Requests'])

    rating.overall_review = rating.overall_review + overview_review
    rating.performance_review = rating.performance_review + performance_review
    # rating += summary_rating
    return rating


def get_result_dict(data, mode):
    result_dict = {}
    tmp_dict = {}
    regex = r"(?P<name>TTFB|DOMContentLoaded|firstPaint|FCP|LCP|Load|TBT|CLS|FirstVisualChange|SpeedIndex|VisualComplete85|LastVisualChange)\:[ ]{0,1}(?P<value>[0-9\.ms]+)"
    matches = re.finditer(regex, data, re.MULTILINE)

    for matchNum, match in enumerate(matches, start=1):
        name = match.group('name')
        value = match.group('value')
        # print('PAIR: ', name, value, '± 10')
        if name not in tmp_dict:
            tmp_dict[name] = list()
        tmp_dict[name].append(value)

    for pair in tmp_dict.items():
        key = pair[0]
        values = pair[1]
        biggest = 0
        total = 0
        value_range = 0
        result = 0
        median = 0
        for value in values:
            number = 0
            if 'ms' in value:
                number = float(value.replace('ms', ''))
            elif 's' in value:
                number = float(
                    value.replace('s', '')) * 1000
            total += number
            if number > biggest:
                biggest = number
            # print('  ', number, total)
        value_count = len(values)
        if value_count < 2:
            value_range = 0
            result = total
        else:
            median = total / value_count
            value_range = biggest - median
            result = median

        tmp = {
            'median': median,
            'range': value_range,
            'mode': mode,
            'points': -1,
            'msg': '- [{2}] {3}: {0:.2f}ms, ±{1:.2f}ms'.format(result, value_range, mode, key),
            'values': values
        }

        if 'SpeedIndex' in key:
            points = 5.0

            adjustment = 500
            if 'mobile' in mode:
                adjustment = 1500

            limit = 500
            # give 0.5 seconds in credit
            speedindex_adjusted = result - adjustment
            if speedindex_adjusted <= 0:
                # speed index is 500 or below, give highest score
                points = 5.0
            else:
                points = 5.0 - ((speedindex_adjusted / limit) * 0.5)
                # points = 5.0 - (speedindex_adjusted / 1000)

            # result_dict['Points'] = points
            tmp['points'] = points

        result_dict[key] = tmp
    return result_dict
