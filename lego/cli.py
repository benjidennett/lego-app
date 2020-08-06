# -------------------------------------------------------------------------------------------------
# Command line interface extensions to the defaults provided by flask.
#
# Provides the following commands:
# - init: Initialises the application database, creates the default users, creates the practice
#       team and sets the stage.
# - secret: Generates a secret key to be used in config.py.
# - add-teams: Add teams to the database.
# - list-teams: List the teams currently in the database.
# - reset-teams: Remove all non-practice teams from the database.
# - stage: Move the stage forwards or backwards. This is for advanced usage only and should not be
#       required while running the event itself.
# -------------------------------------------------------------------------------------------------

from base64 import b64encode
import os
from random import randint, seed

import bcrypt
import click
from sqlalchemy import asc

from lego import app, db
from lego.models import User, Team
from lego.routes import set_active_teams
from tabulate import tabulate

# seed random number generation
seed()


@app.cli.command('init', short_help='Initialise the application.',
    help='Initialise the application by creating the database and the default '
         'users - Admin and Judge.')
@click.option('--admin-password', default='admin')
@click.option('--judge-password', default='judge')
def init_app(admin_password, judge_password):
    click.echo('Initialising application...')
    db.create_all()
    click.echo('Database created.')

    admin = 'Admin'

    judge = 'Judge'

    admin_user = User(username=admin, password=bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()), is_admin=True)
    db.session.add(admin_user)
    judge_user = User(username=judge, password=bcrypt.hashpw(judge_password.encode('utf-8'), bcrypt.gensalt()), is_judge=True)
    db.session.add(judge_user)

    practice_team = Team(number=-1, name='Practice', is_practice=True)
    db.session.add(practice_team)
    
    db.session.commit()
    click.echo('Default users created.')
    click.echo('Practice team created.')

    _set_stage()


@app.cli.command('secret',
    short_help='Generate a secret key to set in config.py.',
    help='Generate a secret key to set in config.py. The key is used to encrypt '
         'the session cookie to prevent session hijacking.')
def secret():
    key = b64encode(os.urandom(64)).decode('utf-8')
    click.echo(key)


@app.cli.command('add-teams',
    short_help='Add teams to the database from a file.',
    help='Add teams to the database from a file. The file should contain one team per line.')
@click.argument('file', type=click.File())
def add_teams(file: str):
    _add_teams(file)

def _add_teams(file: str):
    for line in file:
        line = line.strip()

        if not line:
            continue

        number, name = line.split(',', 2)
        name = name.strip()

        try:
            number = int(number.strip())
            assert number > 0
        except (ValueError, AssertionError):
            click.echo('Invalid number: {!s}'.format(number))
            return

        click.echo('Adding team: {!s} (number: {!s}).'.format(name, number))

        team = Team(number=number, name=name)
        
        db.session.add(team)
        try:
            db.session.commit()
        except:
            click.echo('ERROR: ONE OR MORE TEAMS/TEAM_NUM ALREADY EXIST')
            click.echo(' ')
            click.echo('Have you tried \'flask reset-teams\'? ')
            return
        else:
            click.echo('Team successfully added.')


@app.cli.command('reset-teams',
    short_help='Remove all teams from the database.')
@click.option('-y', is_flag=True, help='Skip confirmation.')
def reset_teams(y: bool):
    no_confirm = y

    if not no_confirm:
        click.echo('All teams will be deleted from the database.')
        click.confirm('Do you wish to continue?', abort=True)

    Team.query.filter_by(is_practice=False).delete()
    db.session.commit()
    click.echo('Teams deleted.')


@app.cli.command('list-teams',
    short_help='List all teams from the database.')
@click.option('--no-practice', is_flag=True, help='Don\'t include the practice team.')
@click.option('--active', is_flag=True, help='Only show teams that aren\'t currently active.')
def list_teams(no_practice: bool, active: bool):
    filters = {}

    if no_practice:
        filters.update({'is_practice': False})

    if active:
        filters.update({'active': True})

    teams = Team.query.filter_by(**filters).order_by(asc('number')).all()

    click.echo('  Number   Name')
    click.echo(' -------- --------------')

    for t in teams:
        click.echo('  {:<6}   {!s}'.format(t.number, t.name))


@app.cli.command('stage', short_help='Set the current stage.',
    help='Set the current stage. this is for advanced usage only and may cause issues if used '
         'during a live event. See the manual for when this should be used.')
def set_stage():
    _set_stage()


def _set_stage(stage: int=None, no_confirm: bool=False):
    '''
    Helper for setting the stage.
    '''

    stage = 0
    return
    # stage_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tmp', '.stage')

    # while True:
    #     if stage is None:
    #         stage = click.prompt('Enter stage (0-4)', default='0')

    #     try:
    #         stage = int(stage)
    #     except ValueError:
    #         click.echo('Invalid value for stage: {!s}'.format(stage))
    #         continue

    #     stages = ('round_1', 'round_2', 'quarter_final', 'semi_final', 'final')
    #     stage_txt = stages[stage]

    #     if app.config['LEGO_APP_TYPE'] == 'bristol' and stage == 1:
    #         click.echo('Round 2 is only available during UK final.\n'
    #                    'If this is not an error, please change your config.py and try again.')
    #         raise click.Abort()

    #     click.echo('You have chosen {!s} ({!s}).'.format(stage_txt, stage))

    #     if no_confirm or click.confirm('Is this correct?'):
    #         try:
    #             with open(stage_file_path, 'w') as fh:
    #                 fh.write(str(stage))
    #         except IOError as e:
    #             click.echo('Could not save stage to file. ({!s})'.format(e))
    #             raise click.Abort()

    #         click.echo('Successfully set stage.')
    #         return


@app.cli.command('simulate', short_help='Simulate a run through the comptition.',
    help='Simulate a run through the competition. Will pause at the end of each round. '
         'WARNING: This will remove any existing teams from the database.')
def simulate():
    # empty the teams first
    click.echo('Resetting teams')
    Team.query.filter_by(is_practice=False).delete()
    db.session.commit()

    # add teams from example file
    click.echo('Adding example teams')
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../teams_example.txt')

    with open(file_path) as fh:
        _add_teams(fh)

    # set the initial stage
    _set_stage(0, True)

    teams = Team.query.filter_by(is_practice=False, active=True).all()

    # round 1
    for _ in range(3):
        for t in teams:
            t.set_score((randint(0, 20) * 10,""))

        db.session.commit()
        click.pause()

    # round 2
    if app.config['LEGO_APP_TYPE'] == 'uk':
        _set_stage(1, True)
        set_active_teams(1)
        teams = Team.query.filter_by(is_practice=False, active=True).all()

        for t in teams:
            t.set_score((randint(0, 20) * 10,""))

        db.session.commit()
        click.pause()

    _set_stage(2, True)
    set_active_teams(2)
    teams = Team.query.filter_by(is_practice=False, active=True).all()

    # quarter + semi
    for i in range(2):
        for t in teams:
            t.set_score((randint(0, 20) * 10,""))

        db.session.commit()
        click.pause()

        _set_stage(3 + i, True)
        set_active_teams(3 + i)
        teams = Team.query.filter_by(is_practice=False, active=True).all()

    # final
    for i in range(2):
        for t in teams:
            t.set_score((randint(0, 20) * 10,""))

        db.session.commit()
        click.pause()


    # remove the used teams
    click.echo('Resetting teams')
    Team.query.filter_by(is_practice=False).delete()
    db.session.commit()

    click.echo('Complete!')


@app.cli.group()
def user():
    pass

@user.command('new')
@click.argument('username')
@click.option('-p','--password', prompt=True, hide_input=True, help='Password for username')
@click.option('--admin',is_flag=True, help='Mark user as an admin')
@click.option('--judge',is_flag=True, help = 'Mark user as a judge')
def create_user(username,password,judge, admin):
    user = User(username=username, password=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()),is_judge= judge,is_admin= admin)
    db.session.add(user)
    db.session.commit()


@user.command('login')
@click.argument('username')
@click.option('-p','--password', prompt=True, hide_input=True, help='Password for username')
def user_login(username,password):
    login=User.authenticate(username, password)

    if isinstance(login, User):
        print('Success')
    else:
        print(login)


@user.command('ls')
def user_ls():
    users = User.query.all()
    table = []

    for user in users:
        table.append([user.id, user.username,user.password,user.is_judge,user.is_admin])

    print(tabulate(table, headers = ["id","username","password","is_judge","is_admin"], tablefmt="orgtbl"))


@user.command('rm')
@click.argument('username')
def rm(username):
    user = User.query.filter_by(username=username).first()
    db.session.delete(user)
    db.session.commit()


