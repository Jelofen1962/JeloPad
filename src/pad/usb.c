#include <string.h>
#include <orbis/libkernel.h>
#include "pad.h"
#include "utils.h"

// Struct to represent attached USB devices via libSceHid
typedef struct usbDriverData {
    bool running;
    int32_t hidHandle;
} usbDriverData;

static usbDriverData globalUsbDriverData = {
    .running = false,
    .hidHandle = -1
};

static int32_t usbSetLightBar(RemotePad *pad, OrbisPadColor *inputColor) {
    (void) pad; (void) inputColor;
    return 0;
}

static int32_t usbResetLightBar(RemotePad *pad) {
    (void) pad;
    return 0;
}

static int32_t usbSetVibration(RemotePad *pad, const OrbisPadVibeParam *param) {
    usbDriverData *ctx = (usbDriverData *)pad->driver->data;
    if (!ctx || !ctx->running || ctx->hidHandle < 0) {
        return 0;
    }

    // Macher Dual Motor Raw Packets
    uint8_t packet_1[8] = {0x01, 0x00, 0x00, param->lgMotor, param->smMotor, 0x00, 0x00, 0x00};
    uint8_t packet_2[8] = {0x02, 0x00, 0x00, param->lgMotor, param->smMotor, 0x00, 0x00, 0x00};

    // Under Open Orbis SDK environment, raw outputs to a custom opened USB HID device
    // are transmitted using the native sceHidWrite API
    // sceHidWrite(ctx->hidHandle, packet_1, sizeof(packet_1));
    // sceHidWrite(ctx->hidHandle, packet_2, sizeof(packet_2));

    return 0;
}

static int32_t usbInit(RemotePadDriverPtr driver) {
    usbDriverData *ctx = (usbDriverData *)driver->data;
    if (ctx->running) {
        return 0;
    }
    
    ctx->running = true;
    final_printf("[JeloPad]: USB physical driver initialized\n");
    return 0;
}

static int32_t usbTerm(RemotePadDriverPtr driver) {
    usbDriverData *ctx = (usbDriverData *)driver->data;
    if (ctx) {
        ctx->running = false;
        ctx->hidHandle = -1;
    }
    return 0;
}

const struct RemotePadDriver usbDriver = {
    .name = "usb",
    .init = usbInit,
    .term = usbTerm,
    .setLightBar = usbSetLightBar,
    .resetLightBar = usbResetLightBar,
    .setVibration = usbSetVibration,
    .data = &globalUsbDriverData
};