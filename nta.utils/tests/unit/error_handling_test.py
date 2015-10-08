#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

"""Unit tests for the error-handling utilities"""

import os
import Queue
import unittest
import logging
import time

from mock import patch, call

from nta.utils import error_handling

from nta.utils.logging_support_raw import LoggingSupport

def setUpModule():
  LoggingSupport.initTestApp()


class ErrorHandlingUtilsTest(unittest.TestCase):
  """ Unit tests for the error-handling utilities """
  
  
  def testAbortProgramOnAnyExceptionWithoutException(self):

    @error_handling.abortProgramOnAnyException(exitCode=2)
    def doSomething(*args, **kwargs):
      return args, kwargs


    inputArgs = (1, 2, 3)
    inputKwargs = dict(a="A", b="B", c="C")

    outputArgs, outputKwargs = doSomething(*inputArgs, **inputKwargs)

    # Validate that doSomething got the right inputs
    self.assertEqual(outputArgs, inputArgs)
    self.assertEqual(outputKwargs, inputKwargs)


  def testAbortProgramOnAnyExceptionWithRuntimeErrorException(self):
    @error_handling.abortProgramOnAnyException(exitCode=2)
    def doSomething(*_args, **_kwargs):
      raise RuntimeError()


    # Patch os._exit and run model in SlotAgent
    osExitCodeQ = Queue.Queue()
    with patch.object(os, "_exit", autospec=True,
                      side_effect=osExitCodeQ.put):
      inputArgs = (1, 2, 3)
      inputKwargs = dict(a="A", b="B", c="C")

      with self.assertRaises(RuntimeError):
        doSomething(*inputArgs, **inputKwargs)

      exitCode = osExitCodeQ.get_nowait()
      self.assertEqual(exitCode, 2)


  def testAbortProgramOnAnyExceptionWithSystemExitException(self):
    # Repeat of the other test, but his time with SystemExit exception,
    # which is derived from BaseException

    @error_handling.abortProgramOnAnyException(exitCode=2)
    def doSomething(*_args, **_kwargs):
      raise SystemExit


    # Patch os._exit and run model in SlotAgent
    osExitCodeQ = Queue.Queue()
    with patch.object(os, "_exit", autospec=True,
                      side_effect=osExitCodeQ.put):
      inputArgs = (1, 2, 3)
      inputKwargs = dict(a="A", b="B", c="C")

      with self.assertRaises(SystemExit):
        doSomething(*inputArgs, **inputKwargs)

      exitCode = osExitCodeQ.get_nowait()
      self.assertEqual(exitCode, 2)

  @patch('time.sleep')
  @patch('time.time')
  def testRetryNoRetries(self, mockTime, mockSleep):
    """ Test that when timeoutSec == 0, function is executed exactly once 
    with no retries, and raises an exception on failure. """    
    
    accumulatedTime = [0]
    
    def testTime():
      return accumulatedTime[0]
    
    def testSleep(duration):
      accumulatedTime[0] += duration  
    
    mockTime.side_effect = testTime
    mockSleep.side_effect = testSleep
    
    _retry = error_handling.retry(timeoutSec=0, initialRetryDelaySec=0.2, 
      maxRetryDelaySec=10)
    fcnExecCounter = [0]
    
    @_retry
    def testFunction():
      fcnExecCounter[0] += 1
      raise Exception("Test exception")
    
    osExitCodeQ = Queue.Queue()
    with patch.object(os, "_exit", autospec=True,
                      side_effect=osExitCodeQ.put):
                      
      with self.assertRaises(Exception):
        testFunction()      
        
    self.assertEqual(mockSleep.mock_calls, [])
    self.assertEqual(fcnExecCounter[0], 1)


  @patch('time.sleep')
  @patch('time.time')
  def testRetryWaitsInitialRetryDelaySec(self, mockTime, mockSleep):
    """ Test that first retry delay is initialRetryDelaySec and subsequent 
    retry delays are geometrically doubling up to maxRetryDelaySec  """
    
    accumulatedTime = [0]
    
    def testTime():
      return accumulatedTime[0]
    
    def testSleep(duration):
      accumulatedTime[0] += duration  
    
    mockTime.side_effect = testTime
    mockSleep.side_effect = testSleep
        
    _retry = error_handling.retry(timeoutSec=30, initialRetryDelaySec=2, 
      maxRetryDelaySec=10)
    fcnExecCounter = [0]
    
    @_retry
    def testFunction():
      fcnExecCounter[0] += 1
      raise Exception("Test exception")
    
    with patch.object(os, "_exit", autospec=True):
      with self.assertRaises(Exception):
        testFunction()      
    
    print fcnExecCounter[0]
    
    self.assertEqual(mockSleep.mock_calls, [call(2), call(4), call(8), 
                                            call(10), call(10)])
    
    # Currently fails due to ENG-78
    self.assertEqual(fcnExecCounter[0], 6)
             

  @patch('time.sleep')
  @patch('time.time')
  def testRetryRetryExceptionIncluded(self, mockTime, mockSleep):
    """ Test that retry is triggered if raised exeception is in 
    retryExceptions """

    accumulatedTime = [0]
    
    def testTime():
      return accumulatedTime[0]
    
    def testSleep(duration):
      accumulatedTime[0] += duration  
    
    mockTime.side_effect = testTime
    mockSleep.side_effect = testSleep
    
    class TestParentException(Exception):
      pass
    
    class TestChildException(TestParentException):
      pass
    
    _retry = error_handling.retry(timeoutSec=1, initialRetryDelaySec=1, 
      maxRetryDelaySec=10, retryExceptions=(TestParentException,))
    
    @_retry
    def testFunction():
      raise TestChildException("Test exception")
    
    with patch.object(os, "_exit", autospec=True):
      with self.assertRaises(Exception):
        testFunction()      
        
    self.assertEqual(mockSleep.call_count, 1)


  @patch('time.sleep')
  @patch('time.time')
  def testRetryRetryExceptionExcluded(self, mockTime, mockSleep):
    """ Test that retry is not triggered if raised exeception is not in 
    retryExceptions """

    accumulatedTime = [0]
    
    def testTime():
      return accumulatedTime[0]
    
    def testSleep(duration):
      accumulatedTime[0] += duration  
    
    mockTime.side_effect = testTime
    mockSleep.side_effect = testSleep
    
    class TestExceptionA(Exception):
      pass
    
    class TestExceptionB(Exception):
      pass
    
    _retry = error_handling.retry(timeoutSec=1, initialRetryDelaySec=1, 
      maxRetryDelaySec=10, retryExceptions=(TestExceptionA,))
    
    @_retry
    def testFunction():
      raise TestExceptionB("Test exception")
    
    with patch.object(os, "_exit", autospec=True):
      with self.assertRaises(TestExceptionB):
        testFunction()      
        
    self.assertEqual(mockSleep.call_count, 0)


  @patch('time.sleep')
  @patch('time.time')
  def testRetryRetryFilter(self, mockTime, mockSleep):
    """ Test that if retryFilter is specified and exception is in retryExceptions,
      retries iff retryFilter returns true """

    accumulatedTime = [0]
    
    def testTime():
      return accumulatedTime[0]
    
    def testSleep(duration):
      accumulatedTime[0] += duration  
    
    mockTime.side_effect = testTime
    mockSleep.side_effect = testSleep
    
    class TestParentException(Exception):
      pass
    
    class TestChildException(TestParentException):
      pass
    
    # Test with retryFilter returning True
    
    _retryTrueFilter = error_handling.retry(timeoutSec=1, initialRetryDelaySec=1, 
      maxRetryDelaySec=10, retryExceptions=(TestParentException,),
      retryFilter=lambda _1, _2, _3: True)
    
    @_retryTrueFilter
    def testFunction():
      raise TestChildException("Test exception")
    
    with patch.object(os, "_exit", autospec=True):
      with self.assertRaises(TestChildException):
        testFunction()      

    self.assertEqual(mockSleep.call_count, 1)

    # Test with retryFilter returning False
    
    mockSleep.reset_mock()
    
    _retryFalseFilter = error_handling.retry(timeoutSec=1, initialRetryDelaySec=1, 
      maxRetryDelaySec=10, retryExceptions=(TestParentException,),
      retryFilter=lambda _1, _2, _3: False)
    
    @_retryFalseFilter
    def testFunction():
      raise TestChildException("Test exception")
    
    with patch.object(os, "_exit", autospec=True):
      with self.assertRaises(TestChildException):
        testFunction()      

    self.assertEqual(mockSleep.call_count, 0)





if __name__ == '__main__':
  unittest.main()

