from functions import *
from pprint import pprint


network_setup_file = 'org.yml'
commands_file = 'commands.yml'

def pull_cpu_usage(ssh_connection):
    command = 'show processes cpu sorted'
    output = send_command(ssh_connection,command)
    output = make_output_list(output)
    for line in output:
        if 'CPU utilization for' in line:
            cpu_use = line.split(';')[-1]
            cpu_use = int(cpu_use.split(' ')[-1][:-1])

    return cpu_use


def make_output_list(output):
    return_this = []
    output = output.split('\n')
    return output

def check_ntp_synch(ssh_connection):
    bad_indicators = ['unsynchronized', 'NTP is not enabled']
    command = commands['show clock'][ssh_connection.device_type]
    output = send_command_text_fsm(ssh_connection,command)
    output = output[0]
    time = "{}/{}/{}/{}: {}".format(output['year'],output['month'],output['day'],output['time'],output['timezone'])
    command = commands['show ntp status'][ssh_connection.device_type]
    output = send_command(ssh_connection,command)
    for item in bad_indicators:
        if item in output:
            return [False, time]
    return [True, time]

def sort_log(ssh_connection):
    bad_lines={}
    bad_indicators = ['DUAL', 'OSPF', 'recursion', 'BGP', 'flapping between port',
    'Duplicate address', 'MACFLAP', 'EIGRP' ]
    command = commands['show logging'][ssh_connection.device_type]
    output = send_command_text_fsm(ssh_connection,command)
    for each in output:
        for line in each['message']:
            for indicator in bad_indicators:
                if indicator in line:
                    if line not in bad_lines:
                        bad_lines[line]=[]
                    tmp_line = "{}/{}/{}".format(each['month'],each['day'], each['time'], line)
                    bad_lines[line].append(tmp_line)
                    
    return bad_lines

def check_bgp(ssh_connection, device):
    command = commands['show bgp neighbors'][ssh_connection.device_type]
    output = send_command_text_fsm(ssh_connection,command)
    issues = []
    for each in output:
        if each['state_pfxrcd'] =='Idle':
            error = '{} is down'.format (each['bgp_neigh'])
            issues.append(error)
        if each['bgp_neigh'] not in device['bgp_nei']:
            error = '{} is an extra BGP nei'.format (each['bgp_neigh'])
            issues.append(error)
    for should_be_here in device['bgp_nei']:
        here=False
        for is_here in output:
            if should_be_here in is_here['bgp_neigh']:
                here = True
        if here == False:
            error= "{} is missing".format(should_be_here)
            issues.append(error)


    return issues



def trouble_shoot_device(device, username, password):
    output = {}
    output['IP']=device["ip"]
    output['Device Name']=device['name']
    ssh_connection = make_connection(device, username, password)
    output['cpu_usage_percent'] = pull_cpu_usage(ssh_connection)
    ntp_tmp_data = check_ntp_synch(ssh_connection)
    output['ntp_working'] = ntp_tmp_data[0]
    output['current_time']= ntp_tmp_data[1]
    output['questionable_log_lines']=sort_log(ssh_connection)
    if 'bgp_nei' in device:
        tmp = check_bgp(ssh_connection, device)
        if len(tmp) != 0:
            output['BGP issues'] = check_bgp(ssh_connection, device)
    return output


username = 'dhimes'
password = 'password'

def tshoot_network(username, password):
    all_data = []
    network_setup = read_in_yaml_file(network_setup_file)
    commands= read_in_yaml_file(commands_file)
    for device in network_setup['dc1']['devices']:
        pprint (device['name'])
        all_data.append(trouble_shoot_device(device, username, password))
    return (all_data)
        

