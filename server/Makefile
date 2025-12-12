CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -O2 -fopenmp
TARGET = server
SOURCE = main.cpp

# Platform detection
UNAME_S := $(shell uname -s 2>/dev/null || echo "Windows")

ifeq ($(UNAME_S),Windows)
    LIBS = -lws2_32
    TARGET := $(TARGET).exe
else
    LIBS = -lpthread
endif

all: $(TARGET)

$(TARGET): $(SOURCE)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SOURCE) $(LIBS)

clean:
	rm -f $(TARGET) $(TARGET).exe

.PHONY: all clean

