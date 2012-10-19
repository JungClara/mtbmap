#!/usr/bin/python
# -*- coding: utf-8 -*-

from map.models import Map
from styles.models import Legend
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.response import TemplateResponse
from django.http import HttpResponse
from django.core.context_processors import csrf
#import mapnik
from map.printing import name_image, map_image, legend_image, scalebar_image, imprint_image
from map.altitude import altitude_image, height
from StringIO import StringIO
from PIL import Image

def index(request):
    maps = Map.objects.all()
    map = maps[0]
    return render_to_response('map/map.html', 
                              {'maps': maps, 'map': map},
                              context_instance=RequestContext(request))

def home(request):
    return TemplateResponse(request, 'map/home.html', {})

def legend(request, zoom):
    zoom = int(zoom)
    legenditems = Legend.objects.all()[0].legend_items(zoom)
    return TemplateResponse(request, 'map/legend.html', {'zoom': zoom, 'legenditems': legenditems})

def exportmap(request):
    c = {}
    c.update(csrf(request))
    try:
#        postquery = request.POST
        zoom = int(request.POST['export_zoom'])
        bounds = request.POST['export_bounds'].replace('(', '').replace(')', '')
    except (KeyError, 'no zoom posted'):
        return render_to_response('map/map.html', {},
                                  context_instance=RequestContext(request))
    else:
        map_title = request.POST['map_title']
        map = Map.objects.get(pk=1)
        bottom = float(bounds.split(',')[1])
        top = float(bounds.split(',')[3])
        left = float(bounds.split(',')[0])
        right = float(bounds.split(',')[2])
        zoom = int(zoom)
        gap = 5
        highres = False
        try:
            highres = request.POST['export_highres']
        except (KeyError, 'highres not checked'):
            highres = False
            map_im = map_image(zoom, left, bottom, right, top, highres)
        else:
            highres = True
            map_im = map_image(zoom, left, bottom, right, top, highres)
        try:
            renderlegend = request.POST['export_legend']
        except (KeyError, 'export_legend not checked'):
            legend_im = Image.new('RGBA', (0, 0), 'white')
        else:
            legend = Legend.objects.all()[0]
            legend_im = legend_image(legend, zoom, gap, 'side', map_im.size[1], highres)
        try:
            renderscale = request.POST['export_scale']
        except (KeyError, 'export_scale not checked'):
            scalebar_im = Image.new('RGBA', (0, 0), 'white')
        else:
            scalebar_im = scalebar_image(zoom, (top+bottom)/2, highres)
        try:
            renderimprint = request.POST['export_imprint']
        except (KeyError, 'export_imprint not checked'):
            imprint_im = Image.new('RGBA', (0, 0), 'white')
        else:
            imprint_im = imprint_image(map.attribution, map_im.size[0], 20, 12, highres)
        if len(map_title)>0:
            name_im = name_image(map_title, map_im.size[0])
        else:
            name_im = Image.new('RGBA', (0, 0), 'white')
        height = map_im.size[1] + name_im.size[1] + scalebar_im.size[1] + imprint_im.size[1]
        width = map_im.size[0] + legend_im.size[0]

        y_base = 0
        im = Image.new('RGBA', (width, height), 'white')
        im.paste(name_im, (map_im.size[0]/2 - name_im.size[0]/2, 0))
        y_base += name_im.size[1]
        im.paste(scalebar_im, (map_im.size[0]/2 - scalebar_im.size[0]/2, y_base))
        y_base += scalebar_im.size[1]
        im.paste(map_im, (0, y_base))
        im.paste(legend_im, (map_im.size[0], y_base))
        y_base += map_im.size[1]
        im.paste(imprint_im, (map_im.size[0]/2 - imprint_im.size[0]/2, y_base))

        response = HttpResponse(mimetype='image/png')
        im.save(response, 'png')
        return response
#        return render_to_response('map/export.html', {'zoom': int(zoom), 'center': center, 'bounds': bounds, 'size': size, 'info': info},
#                                  context_instance=RequestContext(request))
#    zoom = request.POST['export_zoom']
#    c['zoom'] = zoom
#    bounds = request.POST['export_bounds']
#    map_title = request.POST['map_title']
#    return TemplateResponse(request, 'map/export_old.html', c)

def export(request):
    return TemplateResponse(request, 'map/export.html', {})

def profile(request):
    return TemplateResponse(request, 'map/profile.html', {})

def altitudeprofile(request):
    c = {}
    c.update(csrf(request))
    try:
        params = request.POST['profile_params']
    except (KeyError, 'no points posted'):
        return render_to_response('map/map.html', {},
                                  context_instance=RequestContext(request))
    else:
        points = []
        if len(params):
            for part in params.split('),'):
                latlng = part.replace('LatLng(', '').replace(')', '').split(',')
                point = [float(latlng[0]), float(latlng[1])]
                points.append(point)
            im = altitude_image(points)
            try:
                ret = int(im)
            except (AttributeError, 'Not a number'):
                response = HttpResponse(mimetype='image/png')
                im.save(response, 'png')
                return response
            else:
                if ret==-1:
                    message = 'Omlouváme se, nemáme výšková data pro žádanou oblast nebo její část.'
                    return render_to_response('error.html', {'message': message}, context_instance=RequestContext(request))
                else:
                    return render_to_response('map/height.html', {'height': ret}, context_instance=RequestContext(request))
        else:
            message = 'Nezadali jste žádný bod.'
            return render_to_response('error.html', {'message': message}, context_instance=RequestContext(request))

def getheight(request):
    get_value = request.GET['profile_point']
    latlng = get_value.replace('LatLng(', '').replace(')', '').split(',')
    point = [float(latlng[0]), float(latlng[1])]
    point_height = height(point)
    return HttpResponse(point_height, mimetype='text/html')