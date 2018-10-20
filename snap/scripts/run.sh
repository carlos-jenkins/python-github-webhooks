#!/bin/sh

if [ ! -f "$SNAP_COMMON/config.json" ]; then
    cp "$SNAP/config.json.sample" "$SNAP_COMMON/config.json"
fi

if [ ! -L "$SNAP_COMMON/webhooks.py" ]; then
    ln -sf "$SNAP/webhooks.py" "$SNAP_COMMON"
fi

if [ "X$SNAP_ARCH" = "Xamd64" ]; then
  ARCH="x86_64-linux-gnu"
elif [ "X$SNAP_ARCH" = "Xarmhf" ]; then
  ARCH="arm-linux-gnueabihf"
elif [ "X$SNAP_ARCH" = "Xarm64" ]; then
  ARCH="aarch64-linux-gnu"
else
  ARCH="$SNAP_ARCH-linux-gnu"
fi

export PATH=$SNAP/usr/bin:$PATH
export LD_LIBRARY_PATH=$SNAP/usr/lib/$ARCH:$SNAP/usr/lib:$LD_LIBRARY_PATH

cd "$SNAP_COMMON"
mkdir -p hooks

exec env $SNAP/usr/bin/python3 ./webhooks.py $@
