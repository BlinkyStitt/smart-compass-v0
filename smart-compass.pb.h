/* Automatically generated nanopb header */
/* Generated by nanopb-0.3.9.1 at Tue Jun 26 15:56:42 2018. */

#ifndef PB_SMART_COMPASS_PB_H_INCLUDED
#define PB_SMART_COMPASS_PB_H_INCLUDED
#include <pb.h>

/* @@protoc_insertion_point(includes) */
#if PB_PROTO_HEADER_VERSION != 30
#error Regenerate this file with the current version of nanopb generator.
#endif

#ifdef __cplusplus
extern "C" {
#endif

/* Struct definitions */
typedef struct _SmartCompassLocationMessage {
    pb_byte_t network_hash[16];
    pb_byte_t message_hash[16];
    uint32_t tx_peer_id;
    uint32_t tx_time;
    uint32_t tx_ms;
    uint32_t peer_id;
    uint32_t last_updated_at;
    uint32_t hue;
    uint32_t saturation;
    int32_t latitude;
    int32_t longitude;
    uint32_t num_pins;
/* @@protoc_insertion_point(struct:SmartCompassLocationMessage) */
} SmartCompassLocationMessage;

typedef struct _SmartCompassPinMessage {
    pb_byte_t network_hash[16];
    pb_byte_t message_hash[16];
    uint32_t tx_peer_id;
    uint32_t last_updated_at;
    int32_t latitude;
    int32_t longitude;
    uint32_t hue;
    uint32_t saturation;
/* @@protoc_insertion_point(struct:SmartCompassPinMessage) */
} SmartCompassPinMessage;

/* Default values for struct fields */

/* Initializer values for message structs */
#define SmartCompassLocationMessage_init_default {{0}, {0}, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}
#define SmartCompassPinMessage_init_default      {{0}, {0}, 0, 0, 0, 0, 0, 0}
#define SmartCompassLocationMessage_init_zero    {{0}, {0}, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}
#define SmartCompassPinMessage_init_zero         {{0}, {0}, 0, 0, 0, 0, 0, 0}

/* Field tags (for use in manual encoding/decoding) */
#define SmartCompassLocationMessage_network_hash_tag 1
#define SmartCompassLocationMessage_message_hash_tag 2
#define SmartCompassLocationMessage_tx_peer_id_tag 3
#define SmartCompassLocationMessage_tx_time_tag  4
#define SmartCompassLocationMessage_tx_ms_tag    5
#define SmartCompassLocationMessage_peer_id_tag  6
#define SmartCompassLocationMessage_last_updated_at_tag 7
#define SmartCompassLocationMessage_hue_tag      8
#define SmartCompassLocationMessage_saturation_tag 9
#define SmartCompassLocationMessage_latitude_tag 10
#define SmartCompassLocationMessage_longitude_tag 11
#define SmartCompassLocationMessage_num_pins_tag 12
#define SmartCompassPinMessage_network_hash_tag  1
#define SmartCompassPinMessage_message_hash_tag  2
#define SmartCompassPinMessage_tx_peer_id_tag    3
#define SmartCompassPinMessage_last_updated_at_tag 5
#define SmartCompassPinMessage_latitude_tag      6
#define SmartCompassPinMessage_longitude_tag     7
#define SmartCompassPinMessage_hue_tag           8
#define SmartCompassPinMessage_saturation_tag    9

/* Struct field encoding specification for nanopb */
extern const pb_field_t SmartCompassLocationMessage_fields[13];
extern const pb_field_t SmartCompassPinMessage_fields[9];

/* Maximum encoded size of messages (where known) */
#define SmartCompassLocationMessage_size         106
#define SmartCompassPinMessage_size              82

/* Message IDs (where set with "msgid" option) */
#ifdef PB_MSGID

#define SMART_COMPASS_MESSAGES \


#endif

#ifdef __cplusplus
} /* extern "C" */
#endif
/* @@protoc_insertion_point(eof) */

#endif
