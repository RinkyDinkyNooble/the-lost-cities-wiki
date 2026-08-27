package com.rinkynooble.lostcitiesdevtool.chat;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.HoverEvent;
import net.minecraft.network.chat.MutableComponent;

import javax.annotation.Nullable;

import java.util.List;

/**
 * How this mod writes to chat.
 *
 * <p>Minecraft's chat is a bad place to read a report and a worse place to read an
 * error, and most of that is avoidable. Four rules, each answering something that
 * made the old output hard to follow:
 *
 * <ul>
 *   <li><b>One line per fact.</b> A value long enough to wrap produces a second line
 *       with no indent, which reads as a new entry. Long values are cut and the whole
 *       of it goes behind a hover instead.</li>
 *   <li><b>No column alignment.</b> Minecraft's default font is variable width, so
 *       padding with spaces cannot line values up and only looks broken at a
 *       different GUI scale. A dim marker at the head of every line gives the eye a
 *       left edge to track instead.</li>
 *   <li><b>Detail on hover, action on click.</b> A coordinate offers to take you
 *       there, a path offers to copy itself, and a profile key carries the mod's own
 *       description of it.</li>
 *   <li><b>A failure is three things:</b> what went wrong, where, and what to do. In
 *       that order, which is the order the wiki's Error Messages page uses.</li>
 * </ul>
 *
 * <p>Decoration is decoration. If a glyph fails to render, nothing is lost but the
 * look, because every line carries its meaning in the text.
 */
public final class Chat {

    /**
     * Roughly the width of the chat box at default scale, in characters.
     *
     * <p>{@code Licence.MAX_LINE} is the same number and is deliberately a copy:
     * that class holds no Minecraft type so that it can be checked without a server,
     * and importing this one to share an int would end that.
     */
    private static final int WIDTH = 52;

    private static final String RULE = "─".repeat(24);
    private static final String BULLET = "· ";

    private Chat() {
    }

    // ------------------------------------------------------- lines, not sending

    /**
     * The same lines, handed back instead of sent.
     *
     * <p>Not everything that wants this layout has a command source. A message on
     * world join has a player, and building it as one long string with newlines in
     * it is what made that message wrap into unreadable thirds: the client breaks a
     * literal wherever it runs out of room, so a line of a list stops being a line.
     * One component per line is what keeps a list a list.
     */
    public static List<Component> headerLines(String text, String detail) {
        return List.of(Component.literal(RULE).withStyle(ChatFormatting.DARK_GRAY),
                Component.literal(text)
                        .withStyle(ChatFormatting.AQUA, ChatFormatting.BOLD)
                        .append(Component.literal(detail.isEmpty() ? "" : "  " + detail)
                                .withStyle(ChatFormatting.DARK_GRAY)));
    }

    /** One item of a list: a dim bullet and the text. */
    public static Component itemLine(String text) {
        return Component.literal(BULLET).withStyle(ChatFormatting.DARK_GRAY)
                .append(Component.literal(text).withStyle(ChatFormatting.WHITE));
    }

    /** An aside, dim, for context rather than an answer. */
    public static Component noteLine(String text) {
        return Component.literal("  " + text).withStyle(ChatFormatting.DARK_GRAY);
    }

    // ------------------------------------------------------------------ sections

    /** A section heading, with a rule above it so blocks of output separate. */
    public static void header(CommandSourceStack source, String text) {
        send(source, Component.literal(RULE).withStyle(ChatFormatting.DARK_GRAY));
        send(source, Component.literal(text)
                .withStyle(ChatFormatting.AQUA, ChatFormatting.BOLD));
    }

    /** A heading with a trailing detail that is not part of the title. */
    public static void header(CommandSourceStack source, String text, String detail) {
        send(source, Component.literal(RULE).withStyle(ChatFormatting.DARK_GRAY));
        send(source, Component.literal(text)
                .withStyle(ChatFormatting.AQUA, ChatFormatting.BOLD)
                .append(Component.literal("  " + detail)
                        .withStyle(ChatFormatting.DARK_GRAY)));
    }

    // ---------------------------------------------------------------- key, value

    public static void kv(CommandSourceStack source, String key, String value) {
        kv(source, key, value, null);
    }

    /**
     * One fact. {@code hover} is shown over the key, for anything that explains what
     * the key means rather than what this particular value is.
     */
    public static void kv(CommandSourceStack source, String key, String value,
                          @Nullable Component hover) {
        MutableComponent name = Component.literal(key).withStyle(ChatFormatting.GRAY);
        if (hover != null) {
            name = name.withStyle(s -> s
                    .withHoverEvent(new HoverEvent(HoverEvent.Action.SHOW_TEXT, hover))
                    .withUnderlined(true));
        }
        send(source, Component.literal(BULLET).withStyle(ChatFormatting.DARK_GRAY)
                .append(name)
                .append(Component.literal("  ").withStyle(ChatFormatting.DARK_GRAY))
                .append(value(value)));
    }

    /** A fact whose key is a profile key, so the mod's own description is available. */
    public static void profileKey(CommandSourceStack source, String key, String value) {
        kv(source, key, value, describe(key));
    }

    /** The mod's own description of a profile key, plus anything known to be wrong. */
    @Nullable
    public static Component describe(String key) {
        ProfileKeys.Key k = ProfileKeys.get(key);
        if (k == null) {
            return null;
        }
        MutableComponent out = Component.literal(k.name())
                .withStyle(ChatFormatting.AQUA, ChatFormatting.BOLD);

        StringBuilder shape = new StringBuilder();
        if (k.section() != null) {
            shape.append(k.section());
        }
        if (k.type() != null) {
            shape.append(shape.length() > 0 ? ", " : "").append(k.type().toLowerCase());
        }
        if (k.defaultValue() != null) {
            shape.append(shape.length() > 0 ? ", " : "")
                    .append("default ").append(k.defaultValue());
        }
        if (k.min() != null && k.max() != null) {
            shape.append(shape.length() > 0 ? ", " : "")
                    .append(k.min()).append(" to ").append(k.max());
        }
        if (shape.length() > 0) {
            out.append(Component.literal("\n" + shape).withStyle(ChatFormatting.DARK_GRAY));
        }
        if (k.comment() != null) {
            out.append(Component.literal("\n\n" + k.comment())
                    .withStyle(ChatFormatting.WHITE));
        }
        if (k.correction() != null) {
            // The comment is still shown above, because it is what the reader will
            // find in their own config file. This says why not to believe it.
            out.append(Component.literal("\n\nThat comment is wrong.")
                            .withStyle(ChatFormatting.RED, ChatFormatting.BOLD))
                    .append(Component.literal("\n" + k.correction().actually())
                            .withStyle(ChatFormatting.YELLOW))
                    .append(Component.literal("\n\nEvidence: " + k.correction().evidence())
                            .withStyle(ChatFormatting.DARK_GRAY));
        }
        return out;
    }

    // ------------------------------------------------------------------ clickable

    /**
     * A coordinate that offers to take you there.
     *
     * <p>Runs the teleport for an operator and suggests it for everyone else, because
     * a click that fails on a permission check is worse than one that fills the chat
     * box and waits.
     */
    public static void position(CommandSourceStack source, String key,
                                int x, int y, int z) {
        String command = "/tp @s " + x + " " + y + " " + z;
        boolean canRun = source.hasPermission(2);
        Component target = Component.literal(x + " " + y + " " + z)
                .withStyle(s -> s.withColor(ChatFormatting.WHITE)
                        .withUnderlined(true)
                        .withClickEvent(new ClickEvent(canRun
                                ? ClickEvent.Action.RUN_COMMAND
                                : ClickEvent.Action.SUGGEST_COMMAND, command))
                        .withHoverEvent(new HoverEvent(HoverEvent.Action.SHOW_TEXT,
                                Component.literal(canRun
                                        ? "Click to teleport here"
                                        : "Click to put the teleport in your chat box"))));
        send(source, Component.literal(BULLET).withStyle(ChatFormatting.DARK_GRAY)
                .append(Component.literal(key).withStyle(ChatFormatting.GRAY))
                .append(Component.literal("  ").withStyle(ChatFormatting.DARK_GRAY))
                .append(target));
    }

    /**
     * A place in another dimension that offers to take you there.
     *
     * <p>The plain teleport goes to a coordinate in whatever dimension you are
     * already standing in, which for a link to the workshop is the wrong place
     * entirely and looks like the link is broken.
     */
    public static void position(CommandSourceStack source, String key, String label,
                                String dimension, int x, int y, int z) {
        String command = "/execute in " + dimension + " run tp @s "
                + x + " " + y + " " + z;
        boolean canRun = source.hasPermission(2);
        Component target = Component.literal(label)
                .withStyle(st -> st.withColor(ChatFormatting.WHITE)
                        .withUnderlined(true)
                        .withClickEvent(new ClickEvent(canRun
                                ? ClickEvent.Action.RUN_COMMAND
                                : ClickEvent.Action.SUGGEST_COMMAND, command))
                        .withHoverEvent(new HoverEvent(HoverEvent.Action.SHOW_TEXT,
                                Component.literal((canRun ? "Click to go to "
                                        : "Click to put this in your chat box: ")
                                        + x + " " + y + " " + z)
                                        .withStyle(ChatFormatting.GRAY))));
        send(source, Component.literal(BULLET).withStyle(ChatFormatting.DARK_GRAY)
                .append(Component.literal(key).withStyle(ChatFormatting.GRAY))
                .append(Component.literal("  ").withStyle(ChatFormatting.DARK_GRAY))
                .append(target));
    }

    /** A file path that offers to copy itself, since nobody can type one from chat. */
    public static void path(CommandSourceStack source, String key, String path) {
        Component target = Component.literal(shorten(path))
                .withStyle(s -> s.withColor(ChatFormatting.WHITE)
                        .withUnderlined(true)
                        .withClickEvent(new ClickEvent(
                                ClickEvent.Action.COPY_TO_CLIPBOARD, path))
                        .withHoverEvent(new HoverEvent(HoverEvent.Action.SHOW_TEXT,
                                Component.literal(path + "\n\nClick to copy")
                                        .withStyle(ChatFormatting.GRAY))));
        send(source, Component.literal(BULLET).withStyle(ChatFormatting.DARK_GRAY)
                .append(Component.literal(key).withStyle(ChatFormatting.GRAY))
                .append(Component.literal("  ").withStyle(ChatFormatting.DARK_GRAY))
                .append(target));
    }

    // -------------------------------------------------------------------- prose

    /**
     * A sentence, at full width, allowed to wrap.
     *
     * <p>The one-line rule exists so a list of facts stays a list. Prose is not a
     * list, and truncating it hides the answer: a hover only helps a player, and the
     * console and RCON have none.
     */
    public static void prose(CommandSourceStack source, String text) {
        send(source, Component.literal(text).withStyle(ChatFormatting.WHITE));
    }

    /**
     * A line of somebody else's text, reproduced.
     *
     * <p>Indented like a note and not dimmed like one. A note is this mod talking
     * quietly; this is a file being quoted, and dimming it would say the content
     * matters less than the label above it.
     */
    public static void quote(CommandSourceStack source, String text) {
        send(source, Component.literal("  " + text).withStyle(ChatFormatting.WHITE));
    }

    /** An aside. Dim, because it is context rather than an answer. */
    public static void note(CommandSourceStack source, String text) {
        send(source, Component.literal("  " + text).withStyle(ChatFormatting.DARK_GRAY));
    }

    /** Something the reader should act on, but which is not a failure. */
    public static void warn(CommandSourceStack source, String text) {
        send(source, Component.literal("! ").withStyle(ChatFormatting.YELLOW,
                        ChatFormatting.BOLD)
                .append(Component.literal(text).withStyle(ChatFormatting.YELLOW)));
    }

    // ------------------------------------------------------------------ failures

    /**
     * What went wrong, where, and what to do.
     *
     * <p>Any of {@code where} or {@code fix} may be null. A failure with neither is
     * still better than a sentence, because the subject is on its own line.
     */
    public static void fail(CommandSourceStack source, String subject,
                            @Nullable String where, @Nullable String fix) {
        source.sendFailure(Component.literal(subject)
                .withStyle(ChatFormatting.RED, ChatFormatting.BOLD));
        if (where != null) {
            source.sendFailure(Component.literal("  at ")
                    .withStyle(ChatFormatting.DARK_GRAY)
                    .append(Component.literal(where).withStyle(ChatFormatting.RED)));
        }
        if (fix != null) {
            source.sendFailure(Component.literal("  fix ")
                    .withStyle(ChatFormatting.DARK_GRAY)
                    .append(Component.literal(fix).withStyle(ChatFormatting.GREEN)));
        }
    }

    // ------------------------------------------------------------------ internals

    /** A value, cut to one line, with the whole of it on hover when it does not fit. */
    private static Component value(String text) {
        if (text == null) {
            return Component.literal("null").withStyle(ChatFormatting.DARK_GRAY);
        }
        if (text.length() <= WIDTH) {
            return Component.literal(text).withStyle(ChatFormatting.WHITE);
        }
        return Component.literal(text.substring(0, WIDTH - 3) + "...")
                .withStyle(s -> s.withColor(ChatFormatting.WHITE)
                        .withHoverEvent(new HoverEvent(HoverEvent.Action.SHOW_TEXT,
                                Component.literal(text))));
    }

    /** A path cut from the left, because the end of one is the informative half. */
    private static String shorten(String path) {
        return path.length() <= WIDTH ? path
                : "..." + path.substring(path.length() - (WIDTH - 3));
    }

    private static void send(CommandSourceStack source, Component component) {
        source.sendSuccess(() -> component, false);
    }
}
