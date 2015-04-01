#!/usr/bin/env python

import argparse
import sys
import os
import getpass
import glob
import time
import re
import paramiko
import apache_log_parser
import StringIO
import subprocess

class LogFile:

    def __init__(self, log_file):
        self.file_name = log_file
        time_string = re.sub('\.log', '', self.file_name)
        self.time_stamp = time.strptime(time_string, '%Y_%m_%d_%H')
        self.response_data = self.get_response_data()

    def parse_messages(self):
        f = open(self.file_name)
        raw_messages = [line.rstrip('\n') for line in f.readlines()]
        return_array = []
        line_parser = apache_log_parser.make_parser("%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-agent}i\"")
        for raw_message in raw_messages:
            parsed_message = line_parser(raw_message)
            return_array.append({"raw_message": raw_message, "parsed_message": parsed_message})
        return return_array

    def get_response_data(self):
        f = open(self.file_name)
        raw_messages = [line.rstrip('\n') for line in f.readlines()]
        return_array = []
        for raw_message in raw_messages:
            if raw_message == '':
                next
            response = raw_message.split(' ')[8]
            return_array.append({"raw_message": raw_message, "response": response})
        return return_array


    def get_messages_with_response(self, response):
        selected_messages = []
        for mesg_data in self.response_data:
            if mesg_data['response'] == response:
                selected_messages.append(mesg_data['raw_message'])
        return selected_messages

class LogFileCollection:

    def __init__(self, log_file_array):
        self.files = log_file_array
        self.data = [LogFile(log_file_name) for log_file_name in self.files]
        self.index = len(self.data)

    def __iter__(self):
        return self

    def next(self):
        if self.index == 0:
            raise StopIteration
        self.index = self.index - 1
        return self.data[self.index]

    def select_logfiles(self, start_time, stop_time):
        # start_time and stop_time must be time.struct_time objects.
        #assert(type(start_time) is time.struct_time)
        #assert(type(stop_time) is time.struct_time)

        # start_time needs to less than stop_time.
        assert(start_time <= stop_time)

        # find the logfiles.
        times = [time for time in self.data if time.time_stamp >= start_time and time.time_stamp <= stop_time]
        #selected_logs = [logfile.file_name for logfile in times]
        #return LogFileCollection(selected_logs)
        return times

    def print_with_response(self, start_time, end_time, response):
        selected_logs = self.select_logfiles(start_time, end_time)
        for logfile in selected_logs:
           messages = logfile.get_messages_with_response(response)
           for message in messages:
               print(message)

    def send_files(self, start_time, end_time, login_user, remote_host, remote_directory, key_filename):
        selected_logs = self.select_logfiles(start_time, end_time)
        file_names = [logfile.file_name for logfile in selected_logs]
        self._send_with_scp(file_names, login_user, remote_host, remote_directory, key_filename)

    def _send_with_paramiko_sftp(self, login_user, remote_host, remote_directory, key_filename):
        # Get private key
        f = open(key_filename, 'r')
        s = f.read()
        keyfile = StringIO.StringIO(s)
        mykey = paramiko.RSAKey.from_private_key(keyfile)

        #ssh = paramiko.SSHClient()
        #ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #ssh.connect(remote_host, username=login_user, password=None, pkey=mykey, allow_agent=False, look_for_keys=False)
        #sftp = ssh.open_sftp()

        t = paramiko.Transport((remote_host, 22))
        t.connect(username=login_user, pkey=mykey)
        sftp = paramiko.SFTPClient.from_transport(t)
        for logfile in selected_logs:
            sftp.put(logfile.file_name, remote_directory + '/')
        sftp.close()
        ssh.close()

    def _send_with_scp(self, files, login_user, remote_host, remote_directory, key_filename):
        for file in files:
            command = '/usr/bin/scp -i %s -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no %s %s@%s:%s' % (key_filename, file, login_user, remote_host, remote_directory)
            subprocess.call(command, shell=True)


def cmd_line(argv):
    """
    Get the command line arguments and options.
    Global options.
    """
    parser = argparse.ArgumentParser(description='Manage logs')
    parser.add_argument('-p', '--print-with-response', default=None, help='Print messages with specified response.')
    parser.add_argument('-s', '--start-time', default='1943-01-01-00', help='Start time to filter.')
    parser.add_argument('-e', '--end-time', default='9999-01-01-00', help='end time to filter.')
    parser.add_argument('--send-logs', default=None, help='Send logs to host and directory.')
    parser.add_argument('--send-logs-user', default=getpass.getuser(), help='User to login to the remote server as.')
    parser.add_argument('--key-file', default=os.path.expanduser('~/.ssh/id_rsa'), help='Keyfile to use for login to remote server.')
    parser.add_argument('fileglob')

    args = parser.parse_args()
    return args

def main():
    # Get the cmd line.
    args = cmd_line(sys.argv)

    # Convert start_time and end_time strings to time.struct_time.
    start_time = time.strptime(args.start_time, '%Y-%m-%d-%H')
    end_time = time.strptime(args.end_time, '%Y-%m-%d-%H')

    # Get the log files. Exit if there are none.
    files = glob.glob(args.fileglob)
    if files == []:
        print('No files selected.')
        exit(0)

    # Create the LogFileCollection object.
    lfc_obj = LogFileCollection(files)

    # print with responses.
    if args.print_with_response is not None:
        # print all the messages with the specified return code.
        lfc_obj.print_with_response(start_time, end_time, args.print_with_response)

    # send logs to remote host.
    if args.send_logs is not None:
        # send the log files to the host and directory.
        (remote_host, remote_directory) = args.send_logs.split(':')
        lfc_obj.send_files(start_time, end_time, args.send_logs_user, remote_host, remote_directory, args.key_file)

    print('Command completed successfully.')

if __name__ == "__main__":
    main()