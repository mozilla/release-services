import itertools
from flask import Blueprint
from flask import jsonify
from flask import current_app
from flask import abort

bp = Blueprint('jacuzzi-allocator', __name__)

machines = {
    'bld-linux64-ec2-001': {
        'builders': [
            'b2g_b2g-inbound_emulator_dep',
            'Linux birch build',
        ]},
    'bld-linux64-ec2-002': {
        'builders': [
            'Linux b2g-inbound build',
            'Linux b2g-inbound leak test build',
        ]},
    'bld-linux64-ec2-003': {
        'builders': [
            'b2g_b2g-inbound_hamachi_eng_dep',
            'b2g_b2g-inbound_emulator-debug_dep',
        ]},
    'bld-linux64-ec2-004': {
        'builders': [
            'Linux b2g-inbound build',
            'Linux b2g-inbound leak test build',
        ]},
    'bld-linux64-ec2-005': {
        'builders': [
            'b2g_b2g-inbound_hamachi_eng_dep',
            'Linux birch build',
        ]},
    'bld-linux64-ec2-006': {
        'builders': [
            'Linux birch leak test build',
            'Linux x86-64 birch build',
        ]},
    'bld-linux64-ec2-007': {
        'builders': [
            'Linux x86-64 birch leak test build',
        ]},
    'bld-linux64-ec2-008': {
        'builders': [
            'Linux x86-64 birch leak test build',
        ]},
    'bld-linux64-ec2-300': {
        'builders': [
            'b2g_b2g-inbound_emulator_dep',
            'Linux birch build',
        ]},
    'bld-linux64-ec2-301': {
        'builders': [
            'Linux b2g-inbound build',
            'Linux b2g-inbound leak test build',
        ]},
    'bld-linux64-ec2-303': {
        'builders': [
            'b2g_b2g-inbound_hamachi_eng_dep',
            'b2g_b2g-inbound_emulator-debug_dep',
        ]},
    'bld-linux64-ec2-304': {
        'builders': [
            'b2g_b2g-inbound_emulator-debug_dep',
            'b2g_b2g-inbound_emulator_dep',
        ]},
    'bld-linux64-ec2-305': {
        'builders': [
            'Linux birch leak test build',
            'Linux x86-64 birch build',
        ]},
    'bld-linux64-ec2-306': {
        'builders': [
            'Linux birch leak test build',
            'Linux x86-64 birch build',
        ]},
    'bld-linux64-ec2-307': {
        'builders': [
            'Linux x86-64 birch leak test build',
        ]},
    'bld-linux64-spot-001': {
        'builders': [
            'b2g_b2g-inbound_hamachi_eng_dep',
            'b2g_b2g-inbound_emulator-debug_dep',
        ]},
    'bld-linux64-spot-002': {
        'builders': [
            'b2g_b2g-inbound_emulator_dep',
            'Linux birch build',
        ]},
    'bld-linux64-spot-003': {
        'builders': [
            'b2g_b2g-inbound_emulator_dep',
            'Linux birch build',
        ]},
    'bld-linux64-spot-004': {
        'builders': [
            'Linux b2g-inbound build',
            'Linux b2g-inbound leak test build',
        ]},
    'bld-linux64-spot-005': {
        'builders': [
            'Linux b2g-inbound build',
            'Linux b2g-inbound leak test build',
        ]},
    'bld-linux64-spot-006': {
        'builders': [
            'Linux b2g-inbound build',
            'Linux b2g-inbound leak test build',
        ]},
    'bld-linux64-spot-007': {
        'builders': [
            'b2g_b2g-inbound_emulator-debug_dep',
            'b2g_b2g-inbound_emulator_dep',
        ]},
    'bld-linux64-spot-008': {
        'builders': [
            'b2g_b2g-inbound_hamachi_eng_dep',
            'Linux birch build',
        ]},
    'bld-linux64-spot-009': {
        'builders': [
            'Linux birch leak test build',
            'Linux x86-64 birch build',
        ]},
    'bld-linux64-spot-010': {
        'builders': [
            'Linux birch leak test build',
            'Linux x86-64 birch build',
        ]},
    'bld-linux64-spot-011': {
        'builders': [
            'Linux birch leak test build',
            'Linux x86-64 birch build',
        ]},
    'bld-linux64-spot-012': {
        'builders': [
            'Linux x86-64 birch leak test build',
        ]},
    'bld-linux64-spot-013': {
        'builders': [
            'Linux x86-64 birch leak test build',
        ]},
    'bld-linux64-spot-014': {
        'builders': [
            'Linux x86-64 birch leak test build',
        ]},
    'bld-linux64-spot-016': {
        'builders': [
            'b2g_b2g-inbound_hamachi_eng_dep',
            'b2g_b2g-inbound_emulator-debug_dep',
        ]},
    'bld-linux64-spot-300': {
        'builders': [
            'b2g_b2g-inbound_emulator_dep',
            'Linux birch build',
        ]},
    'bld-linux64-spot-301': {
        'builders': [
            'Linux b2g-inbound build',
            'Linux birch build',
        ]},
    'bld-linux64-spot-302': {
        'builders': [
            'Linux b2g-inbound build',
            'Linux b2g-inbound leak test build',
        ]},
    'bld-linux64-spot-303': {
        'builders': [
            'b2g_b2g-inbound_hamachi_eng_dep',
            'b2g_b2g-inbound_emulator-debug_dep',
        ]},
    'bld-linux64-spot-304': {
        'builders': [
            'Linux b2g-inbound build',
            'Linux b2g-inbound leak test build',
        ]},
    'bld-linux64-spot-305': {
        'builders': [
            'Linux b2g-inbound leak test build',
            'b2g_b2g-inbound_hamachi_eng_dep',
        ]},
    'bld-linux64-spot-306': {
        'builders': [
            'b2g_b2g-inbound_emulator-debug_dep',
            'b2g_b2g-inbound_emulator_dep',
        ]},
    'bld-linux64-spot-307': {
        'builders': [
            'b2g_b2g-inbound_emulator-debug_dep',
            'b2g_b2g-inbound_emulator_dep',
        ]},
    'bld-linux64-spot-308': {
        'builders': [
            'b2g_b2g-inbound_hamachi_eng_dep',
            'Linux birch build',
        ]},
    'bld-linux64-spot-309': {
        'builders': [
            'Linux birch leak test build',
            'Linux x86-64 birch build',
        ]},
    'bld-linux64-spot-310': {
        'builders': [
            'Linux birch leak test build',
            'Linux x86-64 birch build',
        ]},
    'bld-linux64-spot-311': {
        'builders': [
            'Linux birch leak test build',
            'Linux x86-64 birch build',
        ]},
    'bld-linux64-spot-312': {
        'builders': [
            'Linux x86-64 birch leak test build',
        ]},
    'bld-linux64-spot-313': {
        'builders': [
            'Linux x86-64 birch leak test build',
        ]},
    'bld-linux64-spot-314': {
        'builders': [
            'Linux x86-64 birch leak test build',
        ]}
}

@bp.route('/v1/allocated/all')
@bp.route('/v1/machines')
def allocated_all():
    return jsonify(machines=machines.keys())

@bp.route('/v1/builders')
def builders():
    all_builders = [m['builders'] for m in machines.values()]
    # flatten
    all_builders = itertools.chain.from_iterable(all_builders)
    # uniquify
    all_builders = list(set(all_builders))
    return jsonify(builders=all_builders)

@bp.route('/v1/builders/<builder>')
def builder(builder):
    matching_machines = [m for m in machines if builder in machines[m]['builders']]
    if not matching_machines:
        abort(404)
    return jsonify(machines=matching_machines)

@bp.route('/v1/machines/<machine>')
def machine(machine):
    if machine not in machines:
        abort(404)
    return jsonify(builders=machines[machine]['builders'])

