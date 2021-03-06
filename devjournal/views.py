# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from flask import render_template, abort, redirect, request, jsonify
from logging import getLogger, DEBUG, INFO, WARN, ERROR
from . import app, db
from .models import Page, ProjectPage, EventPage, Category
from .utils import get_page_and_type, cat_create_if_not_exist, render_page

logger = getLogger(__name__)

@app.route('/')
def index():
    return '<h1>Nothing to see here</h1><p>(For now)</p>'


@app.route('/all')
def all():
    return redirect("/search?q=all")


@app.route('/search')
def search():  # TODO: implement multi-parameters search like "tag:todo and tag:project or name:Hiver"
    if 'q' in request.args:
        query = request.args.get('q')
        results = []
        if ':' not in query:
            if query != "all":
                return "ERROR: please use ?q=tag:mytag \
                        or ?q=name:myname"  # TODO: make a real page
            else:
                results += Page.query.all()
        else:
            t, arg = query.split(':', 2)
            if t == 'tag':
                tag = Category.query.filter_by(name=arg).first()
                if tag is not None:
                    results += Page.query.filter(Page.categories.any(name=tag.name)).all()
            if t == 'name':
                results += Page.query.filter(Page.name.like("%{0}%".format(arg)))
        if len(results) == 1:
            return redirect('/{0}'.format(results[0].name))
        return render_template("search.html", results=results, query=query)
    return render_template("search.html", results=[])

@app.route('/<string:page_name>')
def view(page_name):
    page, t = get_page_and_type(page_name)
    if not page:
        abort(404)
    return render_template('page.html', page=page, page_type=t.__name__)


@app.route('/<string:page_name>/edit', methods=['GET', 'POST'])
def edit(page_name):
    page, t = get_page_and_type(page_name)
    logger.debug("edit: {0}, {1}".format(page, t))
    if not page:
        logger.info("Trying to edit non-existant page {0}. Redirecting to creation".format(page_name))
        return redirect('/{0}/create'.format(page_name))
    if request.method == 'POST':
        logger.debug("edit: sent data: {0}".format(request.get_json()))
        if 'page_name' in request.get_json():
            page.name = request.get_json().get('page_name')
        if 'page_content' in request.get_json():
            page.md = request.json.get('page_content')
        if 'page_categories' in request.get_json():
            page.categories = [cat_create_if_not_exist(cat_name.strip())
                               for cat_name in request.get_json().get(
                'page_categories').split(',')]
        page.save()
        if page.name != page_name:
            return jsonify({'redirect': '/{0}/edit'.format(page.name)})
    return render_page(page)


@app.route('/<string:page_name>/create', methods=['GET', 'POST'])
def create(page_name):
    if request.method == 'POST':
        if 'page_type' not in request.form or 'page_name' not in request.form:
            abort(400)
        if request.form.get('page_type') == 'event':
            page = EventPage()
        elif request.form.get('page_type') == 'project':
            page = ProjectPage()
        else:
            page = Page()
        page.name = page_name
        page.md = ""
        page.save()
        return redirect('/{0}/edit'.format(page_name))
    page, _ = get_page_and_type(page_name)
    if page:
        return redirect('/{0}/edit'.format(page_name))
    return render_template('create.html', page_name=page_name)


@app.route('/<string:page_name>/delete', methods=['GET', 'POST'])
def delete(page_name):
    if request.method == 'POST':
        if 'confirm' in request.form and \
                request.form.get('confirm') == page_name:
            p, _ = get_page_and_type(page_name)
            db.session.delete(p)
            db.commit()
            return redirect('/')
        else:
            return redirect('/{0}'.format(page_name))
    return render_template('delete.html', page_name=page_name)
